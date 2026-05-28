"""Service for device-scoped agent tokens."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import generate_agent_token, hash_agent_token
from app.models.agent_token import AgentToken
from app.models.device import Device


class AgentTokenService:
    """Service for issuing, validating, and revoking agent tokens."""

    @staticmethod
    def create_token(
        db: Session,
        device: Device,
        name: str = "default agent",
    ) -> tuple[str, AgentToken]:
        """Create a device-scoped agent token and persist only its hash."""
        raw_token = generate_agent_token()
        token = AgentToken(
            token_hash=hash_agent_token(raw_token),
            device_id=device.id,
            name=name[:100],
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return raw_token, token

    @staticmethod
    def get_valid_token(db: Session, raw_token: str | None) -> AgentToken | None:
        """Return a non-revoked agent token matching the raw bearer token."""
        if not raw_token or not raw_token.startswith("ztag_"):
            return None

        token_hash = hash_agent_token(raw_token)
        token = db.scalar(
            select(AgentToken).where(
                AgentToken.token_hash == token_hash,
                AgentToken.revoked_at.is_(None),
            )
        )
        if not token:
            return None

        token.last_used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def revoke_token(
        db: Session,
        device_id: int,
        token_id: int,
    ) -> AgentToken | None:
        """Revoke an agent token for a device."""
        token = db.scalar(
            select(AgentToken).where(
                AgentToken.id == token_id,
                AgentToken.device_id == device_id,
                AgentToken.revoked_at.is_(None),
            )
        )
        if not token:
            return None

        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(token)
        return token


agent_token_service = AgentTokenService()
