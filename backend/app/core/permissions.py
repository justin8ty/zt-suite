"""RBAC permissions logic."""

from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.role import Role
from app.models.user import User
from app.services.access_log import access_log_service


class RoleName(str, Enum):
    """Available roles."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


def require_roles(*allowed_roles: str):
    """Dependency that checks if the user has one of the required roles.

    Args:
        *allowed_roles: List of role names that are allowed access.

    Returns:
        Dependency function.
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        user_role_names = [role.name for role in current_user.roles]

        # Check if user has any of the allowed roles
        if not any(role in user_role_names for role in allowed_roles):
            access_log_service.log_access(
                db=db,
                action="access_denied_role",
                status="failure",
                user_id=current_user.id,
                details=f"Required one of {allowed_roles}, but user has {user_role_names}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {allowed_roles}",
            )
        return current_user

    return role_checker


def seed_roles(db: Session) -> None:
    """Seed default roles if they don't exist."""
    roles = [
        {"name": RoleName.ADMIN, "description": "Full access"},
        {"name": RoleName.USER, "description": "Standard user access"},
        {"name": RoleName.VIEWER, "description": "Read-only access"},
    ]

    for role_data in roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)

    db.commit()
