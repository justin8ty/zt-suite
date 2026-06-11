# Zero-Trust Security Suite (ZT Suite)

An FYP zero-trust security implementation for SME environments — identity-centric access control with MFA, endpoint posture verification, network traffic monitoring, and ML-based anomaly detection.

---

## Prerequisites

### Windows

Wireshark is installed for dependency `npcap`.

### Linux

Packet capture requires root privileges or CAP_NET_RAW capability.

When you run sudo command, Linux uses a restricted PATH different from user's path. This introduces conflicts with uv venv configs. To fix it:

```
# cd ../ then /.. back
~/.local/bin/uv run python -c "from src.config import settings; print(f'Output mode: {settings.output_mode}'); print(f'Output file: {settings.output_file}')"
sudo ~/.local/bin/uv run python -m src.main
```

---

## Build / Lint / Test Commands

### Backend

```bash
cd backend
uv sync
uv sync --dev
uv run uvicorn app.main:app --reload
uv run pytest
uv run pytest tests/test_auth.py
uv run pytest tests/test_auth.py::test_login -v
uv run pytest -k "login" -v
uv run pytest --cov=app --cov-report=html
uv run ruff check . && uv run ruff format .
uv run mypy .
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "msg"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
npm test
npm run lint
npm run typecheck
```

### Endpoint Agent

```bash
cd agent
uv sync
sudo uv run python -m src.main
```

### Unit+Int Testing Start

```
# backend
uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
# frontend
npm run dev
# agent
uv sync && uv run python -m src.main
```
