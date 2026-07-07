"""Device and Posture API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentAgentToken, DbSession, get_current_user
from app.core.permissions import RoleName, require_roles
from app.models.device import Device
from app.models.user import User
from app.schemas.agent_token import AgentTokenCreate, AgentTokenIssued, AgentTokenRead
from app.schemas.device import DeviceCreate, DeviceList, DeviceRead
from app.schemas.posture import PostureReportCreate, PostureReportRead
from app.services.agent_token import agent_token_service
from app.services.device import device_service
from app.services.posture import posture_service

router = APIRouter()


def ensure_user_can_manage_device(device: Device, user: User) -> None:
    """Raise if a user cannot manage a device."""
    is_admin = any(r.name == RoleName.ADMIN for r in user.roles)
    if device.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized for this device")


@router.post(
    "",
    response_model=DeviceRead,
    summary="Register a device",
    description="Register a new device or update existing one by hostname.",
)
async def register_device(
    device_in: DeviceCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    """Register device."""
    owner_id = device_in.user_id or current_user.id
    is_admin = any(r.name == RoleName.ADMIN for r in current_user.roles)
    if owner_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can assign device ownership")

    owner = db.get(User, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")

    device = device_service.register(db, device_in, user_id=owner_id)
    return DeviceRead.model_validate(device)


@router.get(
    "",
    response_model=DeviceList,
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.VIEWER))],
    summary="List devices",
    description="List all registered devices. Admin/Viewer only.",
)
async def list_devices(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
) -> DeviceList:
    """List devices."""
    devices, total = device_service.list_devices(db, skip, limit)
    return DeviceList(
        devices=[DeviceRead.model_validate(d) for d in devices], total=total
    )


@router.get(
    "/{device_id}",
    response_model=DeviceRead,
    summary="Get device details",
    description="Get details of a specific device.",
)
async def get_device(
    device_id: int,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    """Get device by ID."""
    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check ownership or admin role
    is_admin = any(r.name == RoleName.ADMIN for r in current_user.roles)
    if device.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this device"
        )

    return DeviceRead.model_validate(device)


@router.post(
    "/{device_id}/agent-tokens",
    response_model=AgentTokenIssued,
    summary="Issue an agent token",
    description="Create a device-scoped token for endpoint agent telemetry reporting.",
)
async def issue_agent_token(
    device_id: int,
    token_in: AgentTokenCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> AgentTokenIssued:
    """Issue a raw agent token once for a registered device."""
    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    ensure_user_can_manage_device(device, current_user)
    raw_token, token = agent_token_service.create_token(db, device, token_in.name)
    return AgentTokenIssued(
        id=token.id,
        device_id=token.device_id,
        name=token.name,
        created_at=token.created_at,
        last_used_at=token.last_used_at,
        revoked_at=token.revoked_at,
        token=raw_token,
    )


@router.delete(
    "/{device_id}/agent-tokens/{token_id}",
    response_model=AgentTokenRead,
    summary="Revoke an agent token",
    description="Revoke a device-scoped agent token.",
)
async def revoke_agent_token(
    device_id: int,
    token_id: int,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> AgentTokenRead:
    """Revoke an agent token for a registered device."""
    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    ensure_user_can_manage_device(device, current_user)
    token = agent_token_service.revoke_token(db, device_id, token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Agent token not found")

    return AgentTokenRead.model_validate(token)


@router.post(
    "/{device_id}/posture",
    response_model=PostureReportRead,
    summary="Submit posture report",
    description="Submit a security posture report for evaluation.",
)
async def submit_posture(
    device_id: int,
    report_in: PostureReportCreate,
    db: DbSession,
    agent_token: CurrentAgentToken,
) -> PostureReportRead:
    """Submit posture report."""
    if agent_token.device_id != device_id:
        raise HTTPException(
            status_code=403, detail="Agent token is not authorized for this device"
        )

    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    report = posture_service.submit_report(db, device, report_in)
    return PostureReportRead.model_validate(report)


@router.get(
    "/{device_id}/posture",
    response_model=PostureReportRead,
    summary="Get latest posture",
    description="Get the most recent posture report for a device.",
)
async def get_latest_posture(
    device_id: int,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> PostureReportRead:
    """Get latest posture report."""
    # Check auth (same as get_device)
    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    is_admin = any(r.name == RoleName.ADMIN for r in current_user.roles)
    if device.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    report = posture_service.get_latest_report(db, device_id)
    if not report:
        raise HTTPException(status_code=404, detail="No posture reports found")

    return PostureReportRead.model_validate(report)
