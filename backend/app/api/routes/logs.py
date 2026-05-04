"""Access Log API routes."""

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import RoleName, require_roles
from app.schemas.log import AccessLogList, AccessLogRead
from app.services.access_log import access_log_service

router = APIRouter()


@router.get(
    "",
    response_model=AccessLogList,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
    summary="List access logs",
    description="Get audit logs. Admin only.",
)
async def list_logs(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    user_id: int | None = None,
    action: str | None = None,
) -> AccessLogList:
    """List access logs."""
    logs, total = access_log_service.get_logs(
        db, skip=skip, limit=limit, user_id=user_id, action=action
    )
    return AccessLogList(
        logs=[AccessLogRead.model_validate(l) for l in logs], total=total
    )
