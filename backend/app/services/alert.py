"""Alert management service."""

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertCreate


class AlertService:
    """Service for alert operations."""

    @staticmethod
    def create_alert(db: Session, alert_in: AlertCreate) -> Alert:
        """Create a new security alert."""
        alert = Alert(
            device_id=alert_in.device_id,
            severity=alert_in.severity,
            category=alert_in.category,
            title=alert_in.title,
            description=alert_in.description,
            source_ip=alert_in.source_ip,
            is_acknowledged=False,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_alerts(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        severity: str | None = None,
        is_acknowledged: bool | None = None,
    ) -> list[Alert]:
        """List alerts with filters."""
        query = select(Alert)

        if severity:
            query = query.where(Alert.severity == severity)
        if is_acknowledged is not None:
            query = query.where(Alert.is_acknowledged == is_acknowledged)

        query = query.order_by(desc(Alert.timestamp)).offset(skip).limit(limit)
        return list(db.execute(query).scalars().all())

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user: User) -> Alert | None:
        """Acknowledge an alert."""
        alert = db.get(Alert, alert_id)
        if not alert:
            return None

        alert.is_acknowledged = True
        alert.acknowledged_by = user.id
        alert.acknowledged_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)
        return alert


alert_service = AlertService()
