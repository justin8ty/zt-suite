# AGENTS.md - Zero-Trust Security Suite (ZT Suite)

## Project Overview

Zero-Trust Security Suite is a software-only security platform for SME environments implementing identity-centric access control with MFA, endpoint posture verification, network traffic monitoring, and ML-based anomaly detection.

---

## Tech Stack

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 + TypeScript (strict mode) |
| Build Tool | Vite 5 |
| Server State | TanStack Query v5 (5-10s polling) |
| Client State | Zustand |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Routing | React Router v6 |
| Forms | React Hook Form + Zod |
| HTTP Client | Axios |

### Backend
| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| Framework | FastAPI 0.109+ |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 (sync) |
| Migrations | Alembic |
| JWT | python-jose[cryptography] |
| MFA/TOTP | pyotp |
| Password Hashing | passlib[argon2] |
| Logging | structlog |
| Server | uvicorn |

### ML / Anomaly Detection
| Component | Technology |
|-----------|------------|
| Core ML | scikit-learn 1.4+ |
| Data Processing | pandas 2.0+, numpy |
| Model Persistence | joblib |

### Database
| Component | Technology |
|-----------|------------|
| Database | SQLite |

### Endpoint Agent
| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| HTTP Client | httpx |
| System Info | psutil, platform |
| Packet Capture | scapy |
| Scheduling | APScheduler |

### DevOps / Tooling
| Component | Technology |
|-----------|------------|
| Package Manager | uv (replaces pip, pip-tools, virtualenv) |
| Testing | pytest + pytest-cov |
| Linting | ruff |
| Type Checking | mypy (strict) |
| Git Hooks | pre-commit |

---

## Build/Lint/Test Commands

### Backend
```bash
cd backend
uv sync                                      # Install dependencies (creates venv automatically)
uv sync --dev                                # Install with dev dependencies
uv run uvicorn app.main:app --reload         # Development server
uv run pytest                                # Run all tests
uv run pytest tests/test_auth.py             # Run single test file
uv run pytest tests/test_auth.py::test_login -v     # Run single test function
uv run pytest -k "login" -v                  # Run tests matching pattern
uv run pytest --cov=app --cov-report=html    # Coverage report
uv run ruff check . && uv run ruff format .  # Lint and format
uv run mypy .                                # Type checking
uv run alembic upgrade head                  # Run migrations
uv run alembic revision --autogenerate -m "msg"     # Create migration
```

### Frontend
```bash
cd frontend
npm install                                  # Install dependencies
npm run dev                                  # Development server (Vite)
npm run build                                # Production build
npm run preview                              # Preview production build
npm test                                     # Run tests
npm run lint                                 # ESLint
npm run typecheck                            # TypeScript check
```

### Endpoint Agent
```bash
cd agent
uv sync                                      # Install dependencies
sudo uv run python -m src.main               # Run agent (requires root for packet capture)
```

---

## Project Structure

```
zt-suite/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/         # Endpoint handlers
│   │   ├── config/             # Settings, logging config
│   │   ├── core/               # Security, permissions, exceptions
│   │   ├── db/
│   │   │   └── migrations/     # Alembic migrations
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic
│   ├── ml/
│   │   ├── models/             # ML model implementations
│   │   ├── training/           # Training scripts
│   │   └── artifacts/          # Saved model files (.joblib)
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── auth/           # Auth-related components
│   │   │   ├── dashboard/      # Dashboard widgets
│   │   │   └── common/         # Shared components
│   │   ├── pages/              # Route pages
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client functions
│   │   ├── stores/             # Zustand stores
│   │   ├── types/              # TypeScript type definitions
│   │   └── lib/                # Utilities
│   └── tests/
│
├── agent/
│   └── src/
│       └── collectors/         # Posture and traffic collectors
│
└── scripts/                    # Dev/deploy helper scripts
```

---

## Code Style Guidelines

### Python (Backend + Agent)

**Imports:** Group as stdlib, third-party, local (blank lines between)

```python
import os
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

from app.services.auth import AuthService
from app.core.exceptions import InvalidCredentialsError
```

**Naming:**
- `snake_case` for variables, functions, modules
- `PascalCase` for classes
- `SCREAMING_SNAKE_CASE` for constants
- `_prefix` for private members

**Types:** Type hints required on all functions, Pydantic for validation

**Errors:** Custom exceptions, specific catches (no bare `except:`), FastAPI HTTPException for API errors

### TypeScript (Frontend)

**Imports:** Group as external libs, internal modules, types. Use path aliases (`@/`).

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { authService } from '@/services/auth';
import type { User } from '@/types/user';
```

**Naming:**
- `camelCase` for variables, functions
- `PascalCase` for components, types, interfaces
- `SCREAMING_SNAKE_CASE` for constants
- `kebab-case` for file names

**Types:** Strict mode enabled, no `any`, explicit return types, Zod for runtime validation

---

## Security Requirements

This is a security product - apply extra rigor:

- **Passwords:** Argon2id only (via passlib)
- **JWT:** 15-minute access token expiry, refresh tokens for renewal
- **Device Trust:** 30-day token for MFA bypass on trusted devices
- **Secrets:** Environment variables only, never commit `.env` files
- **Input:** Validate ALL inputs with Pydantic (backend) and Zod (frontend)
- **SQL:** SQLAlchemy ORM only, no raw string queries
- **Logging:** Structured JSON via structlog, never log passwords/tokens/PII
- **Dependencies:** Regular `pip-audit` and `npm audit` checks

---

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Login Request                                               │
│     POST /api/auth/login { email, password, device_token? }     │
│                                                                 │
│  2. Password Verification                                       │
│     Argon2id hash comparison                                    │
│                                                                 │
│  3. Device Trust Check                                          │
│     If device_token valid and not expired (30 days) → Skip MFA  │
│     Else → Require MFA                                          │
│                                                                 │
│  4. MFA Challenge (if required)                                 │
│     POST /api/auth/mfa { temp_token, totp_code }                │
│                                                                 │
│  5. Token Issuance                                              │
│     Return: access_token (15min), refresh_token, device_token   │
│                                                                 │
│  6. Subsequent Requests                                         │
│     Authorization: Bearer <access_token>                        │
│     Refresh via POST /api/auth/refresh { refresh_token }        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Traffic Capture Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                 Endpoint Agent Packet Capture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scapy sniff on network interface (requires root)               │
│                                                                 │
│  Captured metadata:                                             │
│  - Source/Destination IP                                        │
│  - Source/Destination Port                                      │
│  - Protocol (TCP/UDP)                                           │
│  - Packet size                                                  │
│  - Timestamp                                                    │
│  - TCP flags (SYN, ACK, FIN, RST)                               │
│                                                                 │
│  NOT captured: Payload content                                  │
│                                                                 │
│  Batched every 30-60s → POST /api/traffic                       │
│                                                                 │
│  Backend feature engineering:                                   │
│  - Packets/bytes per minute                                     │
│  - Unique destination count                                     │
│  - Port distribution                                            │
│  - Connection pattern ratios                                    │
│                                                                 │
│  Anomaly detection via Isolation Forest                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Testing Guidelines

- Unit tests for services, integration tests for API routes
- Target >80% coverage on critical paths (auth, RBAC, posture)
- Use pytest fixtures for database and auth setup

```python
# tests/test_auth.py
class TestAuthService:
    def test_login_success(self, db_session, test_user):
        """Should return tokens for valid credentials."""
        result = auth_service.login(
            db_session,
            email="test@example.com",
            password="validpassword"
        )
        assert result.access_token is not None
        assert result.refresh_token is not None

    def test_login_invalid_password(self, db_session, test_user):
        """Should raise InvalidCredentialsError for wrong password."""
        with pytest.raises(InvalidCredentialsError):
            auth_service.login(
                db_session,
                email="test@example.com",
                password="wrongpassword"
            )
```

---

## Performance Requirements

| Operation           | Target   |
|---------------------|----------|
| Authentication      | < 500ms  |
| Dashboard load      | < 2s     |
| Anomaly detection   | < 5s     |
| Posture evaluation  | < 1s     |

---

## Git Conventions

- **Branches:** `feature/`, `fix/`, `refactor/`, `docs/`
- **Commits:** Conventional format - `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- **PR:** Requires passing CI checks (lint, typecheck, tests) before merge

---

## Agent Instructions

1. **Read PRD.md first** for product context and requirements
2. **Prioritize security** - this is a security product
3. **Follow phase plan** - P0 (IAM) -> P1 (Posture) -> P2 (Anomaly) -> P3 (Polish)
4. **Write tests** for all new functionality
5. **Use strict typing** - mypy strict for Python, TypeScript strict for frontend
6. **Validate inputs** at all API boundaries
7. **Log structured JSON** with request IDs via structlog
8. **Never commit secrets** - use `.env` files (gitignored)
9. **Run linters before commit** - ruff for Python, ESLint for TypeScript
