"""Device service."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.schemas.device import DeviceCreate


class DeviceService:
    """Service for device operations."""

    @staticmethod
    def get_by_id(db: Session, device_id: int) -> Device | None:
        """Get device by ID."""
        return db.get(Device, device_id)

    @staticmethod
    def get_by_hostname(db: Session, hostname: str) -> Device | None:
        """Get device by hostname."""
        stmt = select(Device).where(Device.hostname == hostname)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_devices(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
    ) -> tuple[list[Device], int]:
        """List devices."""
        query = select(Device)

        if user_id:
            query = query.where(Device.user_id == user_id)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.execute(count_stmt).scalar() or 0

        query = query.offset(skip).limit(limit)
        devices = list(db.execute(query).scalars().all())

        return devices, total

    @staticmethod
    def register(
        db: Session, device_in: DeviceCreate, user_id: int | None = None
    ) -> Device:
        """Register or update a device.

        If device with hostname exists, update it. Otherwise create new.
        """
        # Simple logic: Identify by hostname for prototype
        # In production, use a hardware UUID or certificate
        device = DeviceService.get_by_hostname(db, device_in.hostname)

        if device:
            # Update existing
            device.os_type = device_in.os_type
            device.os_version = device_in.os_version
            device.agent_version = device_in.agent_version
            device.last_seen = datetime.now(timezone.utc)
            if user_id and not device.user_id:
                device.user_id = user_id
        else:
            # Create new
            device = Device(
                hostname=device_in.hostname,
                os_type=device_in.os_type,
                os_version=device_in.os_version,
                agent_version=device_in.agent_version,
                user_id=user_id,
                is_compliant=False,  # Default to non-compliant until first report
            )
            db.add(device)

        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def update_compliance(db: Session, device: Device, is_compliant: bool) -> None:
        """Update device compliance status."""
        device.is_compliant = is_compliant
        db.commit()
        db.refresh(device)


device_service = DeviceService()
