"""Traffic ingestion service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.traffic import TrafficRecord
from app.schemas.traffic import TrafficBatchCreate


class TrafficService:
    """Service for traffic operations."""

    @staticmethod
    def ingest_batch(db: Session, batch: TrafficBatchCreate) -> int:
        """Ingest a batch of traffic records.

        Returns:
            Number of records inserted.
        """
        # Efficient bulk insert using list of dicts
        # Note: We validate device_id exists at API layer or trust the token owner

        records_data = []
        for record in batch.records:
            data = record.model_dump()
            data["device_id"] = batch.device_id
            records_data.append(data)

        if not records_data:
            return 0

        # Bulk insert (SQLAlchemy 2.0 style)
        db.bulk_insert_mappings(TrafficRecord, records_data)
        db.commit()

        return len(records_data)

    @staticmethod
    def get_traffic(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        device_id: int | None = None,
    ) -> list[TrafficRecord]:
        """List traffic records."""
        query = select(TrafficRecord)

        if device_id:
            query = query.where(TrafficRecord.device_id == device_id)

        query = query.order_by(desc(TrafficRecord.timestamp)).offset(skip).limit(limit)
        return list(db.execute(query).scalars().all())

    @staticmethod
    def cleanup_old_traffic(db: Session, days: int = 7) -> int:
        """Delete traffic records older than N days.

        Returns:
            Number of deleted records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(TrafficRecord).where(TrafficRecord.timestamp < cutoff)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount


traffic_service = TrafficService()
