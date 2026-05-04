"""User service for business logic operations."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service class for user operations."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        """Get a user by ID.

        Args:
            db: Database session.
            user_id: User ID to look up.

        Returns:
            User if found, None otherwise.
        """
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Get a user by email address.

        Args:
            db: Database session.
            email: Email address to look up.

        Returns:
            User if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """List users with pagination.

        Args:
            db: Database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            Tuple of (list of users, total count).
        """
        # Get total count
        count_stmt = select(func.count()).select_from(User)
        total = db.execute(count_stmt).scalar() or 0

        # Get paginated results
        stmt = select(User).offset(skip).limit(limit).order_by(User.id)
        users = list(db.execute(stmt).scalars().all())

        return users, total

    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """Create a new user.

        Args:
            db: Database session.
            user_in: User creation data.

        Returns:
            Created user.

        Raises:
            ValueError: If email already exists.
        """
        # Check if email already exists
        existing = UserService.get_by_email(db, user_in.email)
        if existing:
            raise ValueError(f"Email {user_in.email} already registered")

        # Create user with hashed password
        user = User(
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            is_active=True,
            mfa_enabled=False,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update(db: Session, user: User, user_in: UserUpdate) -> User:
        """Update a user.

        Args:
            db: Database session.
            user: User to update.
            user_in: Update data.

        Returns:
            Updated user.

        Raises:
            ValueError: If new email already exists.
        """
        # Check if new email is taken by another user
        if user_in.email and user_in.email != user.email:
            existing = UserService.get_by_email(db, user_in.email)
            if existing:
                raise ValueError(f"Email {user_in.email} already registered")
            user.email = user_in.email

        if user_in.password:
            user.password_hash = hash_password(user_in.password)

        if user_in.is_active is not None:
            user.is_active = user_in.is_active

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete(db: Session, user: User) -> None:
        """Delete a user (hard delete).

        Args:
            db: Database session.
            user: User to delete.
        """
        db.delete(user)
        db.commit()

    @staticmethod
    def deactivate(db: Session, user: User) -> User:
        """Deactivate a user (soft delete).

        Args:
            db: Database session.
            user: User to deactivate.

        Returns:
            Deactivated user.
        """
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user


# Singleton instance for convenience
user_service = UserService()
