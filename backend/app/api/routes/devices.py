"""Device and Posture API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_current_user
from app.core.permissions import RoleName, require_roles
from app.models.user import User
from app.schemas.device import DeviceCreate, DeviceList, DeviceRead
from app.schemas.posture import PostureReportCreate, PostureReportRead
from app.services.device import device_service
from app.services.posture import posture_service

router = APIRouter()


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
    device = device_service.register(db, device_in, user_id=current_user.id)
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
    "/{device_id}/posture",
    response_model=PostureReportRead,
    summary="Submit posture report",
    description="Submit a security posture report for evaluation.",
)
async def submit_posture(
    device_id: int,
    report_in: PostureReportCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> PostureReportRead:
    """Submit posture report."""
    device = device_service.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check ownership (strict for reporting)
    if device.user_id != current_user.id:
        # In a real agent scenario, the agent might authenticate as itself or the user.
        # For this prototype, we assume the user's token is used by the agent.
        raise HTTPException(
            status_code=403, detail="Not authorized to report for this device"
        )

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
