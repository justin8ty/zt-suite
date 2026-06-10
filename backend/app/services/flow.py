"""Network flow ingestion service."""

from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.flow import NetworkFlow
from app.schemas.flow import NetworkFlowBatchCreate


class NetworkFlowService:
    """Service for scored CICFlowMeter flow operations."""

    @staticmethod
    def ingest_batch(db: Session, batch: NetworkFlowBatchCreate) -> int:
        records_data = []
        for flow in batch.flows:
            data = flow.model_dump(exclude={"raw_features"})
            data["device_id"] = batch.device_id
            data["batch_id"] = flow.batch_id or batch.batch_id
            data["raw_features_json"] = json.dumps(
                flow.raw_features,
                separators=(",", ":"),
                default=str,
            )
            records_data.append(data)

        if not records_data:
            return 0

        db.bulk_insert_mappings(NetworkFlow, records_data)
        db.commit()
        return len(records_data)

    @staticmethod
    def get_flows(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        device_id: int | None = None,
        prediction: int | None = None,
    ) -> list[NetworkFlow]:
        query = select(NetworkFlow)
        if device_id:
            query = query.where(NetworkFlow.device_id == device_id)
        if prediction is not None:
            query = query.where(NetworkFlow.prediction == prediction)
        query = query.order_by(desc(NetworkFlow.timestamp)).offset(skip).limit(limit)
        return list(db.execute(query).scalars().all())


network_flow_service = NetworkFlowService()
