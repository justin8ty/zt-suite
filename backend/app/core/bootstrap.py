"""Application bootstrap logic."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.permissions import seed_roles, RoleName
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User

settings = get_settings()


def create_first_admin(db: Session) -> None:
    """Create the first admin user if no users exist."""
    # Check if any user exists
    if db.query(User).first():
        return

    # Get admin role
    admin_role = db.query(Role).filter(Role.name == RoleName.ADMIN).first()
    if not admin_role:
        # Should be seeded already, but just in case
        seed_roles(db)
        admin_role = db.query(Role).filter(Role.name == RoleName.ADMIN).first()

    user = User(
        email=settings.first_admin_email,
        password_hash=hash_password(settings.first_admin_password),
        is_active=True,
        mfa_enabled=False,
    )
    user.roles.append(admin_role)

    db.add(user)
    db.commit()
