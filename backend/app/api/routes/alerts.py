"""Alert API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentAgentToken, DbSession, get_current_user
from app.core.permissions import RoleName, require_roles
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertRead, AlertUpdate
from app.services.alert import alert_service
from app.services.device import device_service

router = APIRouter()


@router.post(
    "",
    response_model=AlertRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert",
    description="Report a security alert/anomaly.",
)
async def create_alert(
    alert_in: AlertCreate,
    db: DbSession,
    agent_token: CurrentAgentToken,
) -> AlertRead:
    """Create alert."""
    if agent_token.device_id != alert_in.device_id:
        raise HTTPException(
            status_code=403, detail="Agent token is not authorized for this device"
        )

    device = device_service.get_by_id(db, alert_in.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    alert = alert_service.create_alert(db, alert_in)
    return AlertRead.model_validate(alert)


@router.get(
    "",
    response_model=list[AlertRead],
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.VIEWER))],
    summary="List alerts",
    description="Get security alerts.",
)
async def list_alerts(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1),
    severity: str | None = None,
    is_acknowledged: bool | None = None,
) -> list[AlertRead]:
    """List alerts."""
    return alert_service.get_alerts(db, skip, limit, severity, is_acknowledged)


@router.patch(
    "/{alert_id}",
    response_model=AlertRead,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
    summary="Acknowledge alert",
    description="Mark an alert as acknowledged. Admin only.",
)
async def acknowledge_alert(
    alert_id: int,
    update_in: AlertUpdate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> AlertRead:
    """Acknowledge alert."""
    if not update_in.is_acknowledged:
        # We only support acknowledging for now
        raise HTTPException(status_code=400, detail="Can only acknowledge alerts")

    alert = alert_service.acknowledge_alert(db, alert_id, current_user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertRead.model_validate(alert)
