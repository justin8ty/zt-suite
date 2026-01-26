"""Protected Resource Demo API routes."""

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_compliant_device, require_mfa
from app.core.permissions import RoleName, require_roles
from app.models.device import Device
from app.models.user import User
from app.services.access_log import access_log_service

router = APIRouter()


@router.get(
    "/files",
    summary="Access Protected Files",
    description="Demo endpoint protected by full Zero-Trust chain (Auth + MFA + Role + Posture).",
)
async def get_protected_files(
    db: DbSession,
    current_user: User = Depends(require_mfa),
    device: Device = Depends(get_compliant_device),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.USER)),
) -> dict[str, object]:
    """Get protected files list.

    Access requires:
    1. Authenticated User (handled by get_current_user/require_mfa)
    2. MFA Enabled (require_mfa)
    3. Compliant Device (get_compliant_device)
    4. Valid Role (require_roles)
    """

    # Log success
    access_log_service.log_access(
        db=db,
        action="resource_access_granted",
        status="success",
        user_id=current_user.id,
        resource="/api/protected/files",
        details=f"Device: {device.hostname}, ID: {device.id}",
    )

    return {
        "message": "Access Granted",
        "user": current_user.email,
        "device": device.hostname,
        "files": [
            {"name": "confidential_report.pdf", "size": "2.4MB", "sensitivity": "high"},
            {
                "name": "employee_salaries.xlsx",
                "size": "1.1MB",
                "sensitivity": "restricted",
            },
            {
                "name": "project_blueprint.cad",
                "size": "45MB",
                "sensitivity": "confidential",
            },
        ],
    }
