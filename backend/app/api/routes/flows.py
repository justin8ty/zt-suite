"""Network flow API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentAgentToken, DbSession
from app.core.permissions import RoleName, require_roles
from app.schemas.flow import NetworkFlowBatchCreate, NetworkFlowRead
from app.services.device import device_service
from app.services.flow import network_flow_service

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest scored network flows",
    description="Bulk upload CICFlowMeter-derived, model-scored flows from an agent.",
)
async def ingest_flows(
    batch: NetworkFlowBatchCreate,
    db: DbSession,
    agent_token: CurrentAgentToken,
) -> dict[str, int]:
    """Ingest scored network flows."""
    if agent_token.device_id != batch.device_id:
        raise HTTPException(
            status_code=403, detail="Agent token is not authorized for this device"
        )

    device = device_service.get_by_id(db, batch.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    count = network_flow_service.ingest_batch(db, batch)
    return {"inserted": count}


@router.get(
    "/count",
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.VIEWER))],
    summary="Count scored network flows",
    description="Get the total number of CICFlowMeter-derived flow records. Admin/Viewer only.",
)
async def count_flows(
    db: DbSession,
    device_id: int | None = None,
    prediction: int | None = None,
) -> dict[str, int]:
    """Count scored network flows."""
    return {"total": network_flow_service.count_flows(db, device_id, prediction)}


@router.get(
    "",
    response_model=list[NetworkFlowRead],
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.VIEWER))],
    summary="List scored network flows",
    description="Get CICFlowMeter-derived flow records. Admin/Viewer only.",
)
async def list_flows(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    device_id: int | None = None,
    prediction: int | None = None,
) -> list[NetworkFlowRead]:
    """List scored network flows."""
    flows = network_flow_service.get_flows(db, skip, limit, device_id, prediction)
    return [NetworkFlowRead.model_validate(flow) for flow in flows]
