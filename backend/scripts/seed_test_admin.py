"""Seed a dedicated non-MFA admin for frontend integration tests.

Run this after the backend has started once (so tables and roles exist):

    cd backend
    uv run python scripts/seed_test_admin.py
"""

import sys
import os

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.core.permissions import RoleName
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.role import Role
from app.models.user import User  # noqa: F401 – register model

TEST_ADMIN_EMAIL = "testadmin@zt-suite.dev"
TEST_ADMIN_PASSWORD = "integration-test-pw-123!"


def main() -> None:
    settings = get_settings()
    print(f"Using database: {settings.database_url}")

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Ensure roles exist
        admin_role = db.query(Role).filter(Role.name == RoleName.ADMIN).first()
        if not admin_role:
            from app.core.permissions import seed_roles
            seed_roles(db)
            admin_role = db.query(Role).filter(Role.name == RoleName.ADMIN).first()

        if not admin_role:
            print("ERROR: Could not find or create admin role.")
            sys.exit(1)

        # Check if test admin already exists
        existing = db.query(User).filter(User.email == TEST_ADMIN_EMAIL).first()
        if existing:
            print(f"Test admin '{TEST_ADMIN_EMAIL}' already exists (id={existing.id}). Skipping.")
            # Ensure MFA is disabled
            if existing.mfa_enabled:
                existing.mfa_enabled = False
                existing.mfa_secret = None
                db.commit()
                print("  → MFA disabled on existing account.")
            return

        # Create the test admin user (MFA disabled, no secret, active)
        user = User(
            email=TEST_ADMIN_EMAIL,
            password_hash=hash_password(TEST_ADMIN_PASSWORD),
            is_active=True,
            mfa_enabled=False,
            mfa_secret=None,
        )
        user.roles.append(admin_role)
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"Created test admin: '{TEST_ADMIN_EMAIL}' (id={user.id})")
        print(f"  Password: {TEST_ADMIN_PASSWORD}")
        print(f"  MFA: disabled")


if __name__ == "__main__":
    main()
