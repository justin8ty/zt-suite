"""Traffic API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_current_user
from app.core.permissions import RoleName, require_roles
from app.models.user import User
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
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Ingest traffic records."""
    # Verify device exists and belongs to user
    device = device_service.get_by_id(db, batch.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.user_id != current_user.id:
        # In production, agent authentication would be separate.
        # For now, agent uses user's token.
        raise HTTPException(status_code=403, detail="Not authorized for this device")

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
