"""Access logging service."""

from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.access_log import AccessLog


class AccessLogService:
    """Service for access logs."""

    @staticmethod
    def log_access(
        db: Session,
        action: str,
        status: str,
        user_id: int | None = None,
        resource: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: str | None = None,
    ) -> AccessLog:
        """Create a new audit log entry.

        Args:
            db: Database session.
            action: Event name.
            status: "success" or "failure".
            user_id: ID of user (if known).
            resource: Target endpoint/resource.
            ip_address: Client IP.
            user_agent: Client User-Agent.
            details: Extra info.

        Returns:
            Created AccessLog.
        """
        log_entry = AccessLog(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def get_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
        action: str | None = None,
    ) -> tuple[list[AccessLog], int]:
        """List access logs with optional filters."""
        query = select(AccessLog)

        if user_id:
            query = query.where(AccessLog.user_id == user_id)
        if action:
            query = query.where(AccessLog.action == action)

        # Count total matches
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.execute(count_stmt).scalar() or 0

        # Get paginated results
        query = query.order_by(desc(AccessLog.timestamp)).offset(skip).limit(limit)
        logs = list(db.execute(query).scalars().all())

        return logs, total


access_log_service = AccessLogService()
