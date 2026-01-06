# ZT Suite Development Checklist

This checklist tracks implementation progress against PRD requirements.

---

## Phase 0 - MVP (IAM, MFA, RBAC, Basic Dashboard)

### Backend Setup
- [ ] Initialize FastAPI project structure
- [ ] Configure SQLAlchemy + SQLite database
- [ ] Set up Alembic migrations
- [ ] Configure structlog for JSON logging
- [ ] Create Pydantic settings (environment variables)

### User Management
- [ ] User model (id, email, password_hash, is_active, created_at)
- [ ] Create user endpoint (POST /api/users)
- [ ] Get user endpoint (GET /api/users/{id})
- [ ] List users endpoint (GET /api/users)
- [ ] Update user endpoint (PATCH /api/users/{id})
- [ ] Delete user endpoint (DELETE /api/users/{id})

### Authentication
- [ ] Password hashing with Argon2id
- [ ] Login endpoint (POST /api/auth/login)
- [ ] JWT access token generation (15-min expiry)
- [ ] JWT refresh token generation
- [ ] Token refresh endpoint (POST /api/auth/refresh)
- [ ] Logout endpoint (POST /api/auth/logout)
- [ ] Protected route middleware (verify JWT)

### MFA (TOTP)
- [ ] TOTP secret generation per user
- [ ] QR code generation for authenticator apps
- [ ] MFA enrollment endpoint (POST /api/auth/mfa/enroll)
- [ ] MFA verification endpoint (POST /api/auth/mfa/verify)
- [ ] Temporary token for MFA-pending state

### Device Trust
- [ ] Device model (id, user_id, token_hash, created_at, expires_at)
- [ ] Generate device trust token on successful MFA
- [ ] Validate device token on login (skip MFA if valid)
- [ ] 30-day expiry for device tokens
- [ ] Revoke device endpoint (DELETE /api/devices/{id})

### RBAC
- [ ] Role model (id, name, permissions)
- [ ] User-Role association
- [ ] Default roles (admin, user, viewer)
- [ ] Permission constants/enums
- [ ] Role-based route protection decorator
- [ ] Assign role endpoint (POST /api/users/{id}/roles)

### Access Logging
- [ ] Access log model (id, user_id, action, resource, timestamp, ip, status)
- [ ] Log all authentication attempts
- [ ] Log all access decisions
- [ ] Get logs endpoint (GET /api/logs) - admin only

### Frontend Setup
- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Set up React Router
- [ ] Configure TanStack Query
- [ ] Create Axios instance with interceptors
- [ ] Set up Zustand auth store

### Frontend Auth Pages
- [ ] Login page (email + password form)
- [ ] MFA challenge page (TOTP input)
- [ ] MFA enrollment page (QR code display)
- [ ] Password reset page (if applicable)
- [ ] Protected route wrapper component

### Basic Dashboard
- [ ] Dashboard layout (sidebar, header, content area)
- [ ] Dashboard home page (summary stats)
- [ ] Users list page (admin only)
- [ ] User detail/edit page
- [ ] Activity logs page
- [ ] Basic navigation

### Testing (P0)
- [ ] Auth service unit tests
- [ ] MFA service unit tests
- [ ] JWT service unit tests
- [ ] Login API integration tests
- [ ] RBAC permission tests
- [ ] Frontend auth flow E2E test (optional)

---

## Phase 1 - Enhancement (Endpoint Posture, Logging)

### Endpoint Agent
- [ ] Initialize agent project structure
- [ ] Agent configuration (backend URL, API key, intervals)
- [ ] System info collector (OS, version, architecture)
- [ ] Patch level detection
- [ ] Antivirus presence check
- [ ] Posture report scheduler (APScheduler)
- [ ] HTTP client to backend (httpx)

### Backend Posture Module
- [ ] Device/Endpoint model (id, user_id, hostname, os, last_seen)
- [ ] Posture report model (id, device_id, os_version, patch_level, av_status, timestamp)
- [ ] Posture ingestion endpoint (POST /api/posture)
- [ ] Posture evaluation service (compliance rules)
- [ ] Get device posture endpoint (GET /api/devices/{id}/posture)
- [ ] List devices endpoint (GET /api/devices)
- [ ] Compliance status calculation

### Posture-Based Access Control
- [ ] Check posture before granting access
- [ ] Block non-compliant devices
- [ ] Posture compliance in access logs

### Enhanced Logging
- [ ] Request ID middleware
- [ ] Structured log format (JSON)
- [ ] Log levels (INFO, WARN, ERROR)
- [ ] Sensitive data filtering (passwords, tokens)
- [ ] Log retention policy (if applicable)

### Dashboard Updates
- [ ] Devices list page
- [ ] Device detail page (posture history)
- [ ] Compliance overview widget
- [ ] Compliance status indicators (compliant/non-compliant)

### Testing (P1)
- [ ] Posture service unit tests
- [ ] Posture API integration tests
- [ ] Agent posture collector tests
- [ ] Compliance evaluation tests

---

## Phase 2 - Optimization (Anomaly Detection)

### Traffic Capture (Agent)
- [ ] Scapy packet capture implementation
- [ ] Filter for TCP/UDP traffic
- [ ] Extract metadata (src/dst IP, ports, protocol, size, flags)
- [ ] Batch traffic records (30-60s intervals)
- [ ] POST traffic data to backend

### Backend Traffic Module
- [ ] Traffic record model (id, device_id, src_ip, dst_ip, src_port, dst_port, protocol, size, timestamp)
- [ ] Traffic ingestion endpoint (POST /api/traffic)
- [ ] Traffic aggregation service
- [ ] Get traffic endpoint (GET /api/traffic) - with filters

### Feature Engineering
- [ ] Packets per minute calculation
- [ ] Bytes per minute calculation
- [ ] Unique destination count
- [ ] Port distribution analysis
- [ ] Connection pattern ratios (SYN/FIN/RST)
- [ ] Feature vector generation per time window

### Anomaly Detection Model
- [ ] Isolation Forest model implementation
- [ ] Training script with baseline data
- [ ] Model persistence (joblib)
- [ ] Model loading on startup
- [ ] Inference service (score traffic features)
- [ ] Anomaly threshold configuration

### Alert System
- [ ] Alert model (id, type, severity, device_id, description, timestamp, acknowledged)
- [ ] Alert generation on anomaly detection
- [ ] Severity levels (low, medium, high, critical)
- [ ] Get alerts endpoint (GET /api/alerts)
- [ ] Acknowledge alert endpoint (PATCH /api/alerts/{id})
- [ ] Brute-force detection (failed login threshold)

### Dashboard Updates
- [ ] Alerts list page
- [ ] Alert detail page
- [ ] Alert acknowledgment workflow
- [ ] Traffic visualization (charts)
- [ ] Anomaly score display
- [ ] Real-time alert notifications (polling)

### Testing (P2)
- [ ] Feature engineering unit tests
- [ ] Anomaly detection model tests
- [ ] Traffic ingestion API tests
- [ ] Alert generation tests

---

## Phase 3 - Innovation (Explainability, UI Refinement)

### Explainable Anomaly Detection
- [ ] Reason codes for anomalies (e.g., "traffic spike", "unusual port")
- [ ] Feature contribution scores
- [ ] Human-readable explanations
- [ ] Explanation in alert details

### UI/UX Refinement
- [ ] Dashboard layout polish
- [ ] Responsive design
- [ ] Loading states and skeletons
- [ ] Error handling and messages
- [ ] Empty states
- [ ] Accessibility improvements
- [ ] Dark mode (optional)

### Data Visualization
- [ ] Traffic trends chart (time series)
- [ ] Anomaly score history chart
- [ ] Compliance pie chart
- [ ] User activity heatmap (optional)
- [ ] Alert severity distribution

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide for administrators
- [ ] Deployment guide
- [ ] Agent installation guide

### Final Testing
- [ ] Full integration test suite
- [ ] Performance testing (auth <500ms, dashboard <2s)
- [ ] Security testing (input validation, auth bypass attempts)
- [ ] Coverage report (target >80% critical paths)

---

## KPI Validation Checklist

- [ ] ≥95% authentication attempts protected by MFA
- [ ] ≥90% endpoint compliance detection accuracy
- [ ] ≥80% precision in anomaly detection
- [ ] <2s dashboard data refresh latency
- [ ] 100% access events logged and auditable

---

## Security Checklist

- [ ] Argon2id for all password hashing
- [ ] JWT access tokens expire in 15 minutes
- [ ] Device trust tokens expire in 30 days
- [ ] No secrets in codebase (use .env)
- [ ] All inputs validated (Pydantic/Zod)
- [ ] SQL injection prevention (SQLAlchemy ORM only)
- [ ] No sensitive data in logs
- [ ] TLS for all communications (production)

---

## Notes

- Update this checklist as tasks are completed
- Each checkbox can be marked with `[x]` when done
- Add sub-tasks as needed during implementation
