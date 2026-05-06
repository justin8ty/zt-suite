"""Persistent local identity for the endpoint agent."""

from pathlib import Path
from uuid import uuid4

from src.config import settings


def get_agent_id() -> str:
    """Return configured or locally persisted agent ID.

    The backend needs a stable endpoint identifier. If one is explicitly
    configured, use it. Otherwise generate a UUID once and persist it to the
    configured state directory.
    """
    if settings.agent_id:
        return settings.agent_id

    state_dir = Path(settings.agent_state_dir)
    agent_id_path = state_dir / "agent_id"

    if agent_id_path.exists():
        existing = agent_id_path.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    state_dir.mkdir(parents=True, exist_ok=True)
    generated = str(uuid4())
    agent_id_path.write_text(generated + "\n", encoding="utf-8")
    return generated
