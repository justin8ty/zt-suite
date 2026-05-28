"""Traffic API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentAgentToken, DbSession
from app.core.permissions import RoleName, require_roles
from app.schemas.traffic import TrafficBatchCreate, TrafficRecordRead
from app.services.device import device_service
from app.services.traffic import traffic_service

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest traffic batch",
    description="Bulk upload traffic records from an agent.",
)
async def ingest_traffic(
    batch: TrafficBatchCreate,
    db: DbSession,
    agent_token: CurrentAgentToken,
) -> dict[str, int]:
    """Ingest traffic records."""
    if agent_token.device_id != batch.device_id:
        raise HTTPException(
            status_code=403, detail="Agent token is not authorized for this device"
        )

    device = device_service.get_by_id(db, batch.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    count = traffic_service.ingest_batch(db, batch)
    return {"inserted": count}


@router.get(
    "",
    response_model=list[TrafficRecordRead],
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.VIEWER))],
    summary="List traffic history",
    description="Get traffic records. Admin/Viewer only.",
)
async def list_traffic(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    device_id: int | None = None,
) -> list[TrafficRecordRead]:
    """List traffic."""
    return traffic_service.get_traffic(db, skip, limit, device_id)
