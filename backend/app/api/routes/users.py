"""User API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_current_user
from app.core.permissions import RoleName, require_roles
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleRead
from app.schemas.user import UserCreate, UserList, UserRead, UserUpdate
from app.services.user import user_service

router = APIRouter()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. This endpoint is public for self-registration.",
)
async def create_user(
    user_in: UserCreate,
    db: DbSession,
) -> UserRead:
    """Create a new user account.

    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    """
    try:
        user = user_service.create(db, user_in)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=UserList,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
    summary="List all users",
    description="Get a paginated list of all users. Requires admin role.",
)
async def list_users(
    db: DbSession,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
) -> UserList:
    """List all users with pagination."""
    users, total = user_service.list_users(db, skip=skip, limit=limit)
    return UserList(
        users=[UserRead.model_validate(u) for u in users],
        total=total,
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Get a specific user's details by their ID.",
)
async def get_user(
    user_id: int,
    db: DbSession,
) -> UserRead:
    """Get a user by ID."""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return UserRead.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user",
    description="Update a user's details. Users can update their own profile, admins can update anyone.",
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: DbSession,
) -> UserRead:
    """Update a user's details."""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    try:
        updated_user = user_service.update(db, user, user_in)
        return UserRead.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
    summary="Delete user",
    description="Delete a user account. Requires admin role.",
)
async def delete_user(
    user_id: int,
    db: DbSession,
) -> None:
    """Delete a user by ID."""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    user_service.delete(db, user)


@router.post(
    "/{user_id}/roles",
    response_model=UserRead,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
    summary="Assign role to user",
    description="Assign a role to a user. Requires admin role.",
)
async def assign_role(
    user_id: int,
    role_name: RoleName,
    db: DbSession,
) -> UserRead:
    """Assign role to user."""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    # Get role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )

    # Assign role if not already assigned
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)

    return UserRead.model_validate(user)
