# ZT Suite Endpoint Agent

The `/agent` package is the endpoint-side component of the Zero-Trust Security Suite. It is intended to run locally on SME endpoints as a long-running, headless background service/daemon.

Its role is to collect endpoint telemetry, monitor network metadata, perform local feature engineering and anomaly detection, then report posture, traffic, and alerts to the central ZT Suite backend.

## Purpose

The agent is the "sensor + local detection" layer of the platform:

```text
Endpoint Agent -> Backend API -> Admin Dashboard
```

It should eventually be installed on each protected endpoint and run continuously, independent of whether a user is logged in.

The agent should support the project's Zero-Trust goals by providing:

- endpoint posture verification
- internal network traffic visibility
- local anomaly detection
- alert generation
- reliable reporting to the backend

## Correct Runtime Abstraction

The correct abstraction is **an OS background service/daemon**, not a normal desktop app.

Python is the implementation language, but the product abstraction should be:

```text
ZT Suite Agent = endpoint background service
Implemented in Python
Installed as systemd service on Linux / Windows Service on Windows
```

This is preferred because an endpoint security agent should:

- start automatically on boot
- run without a logged-in user
- survive user logout
- restart after crashes
- run with controlled elevated privileges where needed
- perform continuous monitoring
- report to the backend in the background

A normal Win32 background/tray application is easier to build, but it is not ideal as the core agent because it only runs after user login, can be closed more easily, and is weaker for enterprise/security deployment. A tray app could be added later only as an optional status/control companion.

## Recommended Tech Stack

Current and recommended stack:

| Area | Technology |
|---|---|
| Runtime | Python 3.11+ preferred for project alignment |
| Dependency management | `uv` |
| Packet capture | Scapy |
| System telemetry | `psutil`, `platform`, `socket` |
| Scheduling | APScheduler |
| HTTP client | `httpx` |
| Data validation | Pydantic |
| Local buffering | SQLite |
| ML inference | `joblib`, `scikit-learn`, `numpy` |
| Logging | structured JSON logging, ideally `structlog` |
| Linux service | systemd |
| Windows service | Windows Service via NSSM, WinSW, or `pywin32` |
| Packaging | PyInstaller or Nuitka for deployable binaries |

For this FYP, the most practical deployment path is:

```text
Python source during development
-> PyInstaller/Nuitka executable later
-> systemd service on Linux
-> Windows Service using NSSM/WinSW on Windows
```

## Current Implementation Status

The current agent implementation already contains a basic traffic capture pipeline:

```text
agent/src/main.py
agent/src/config.py
agent/src/collectors/traffic.py
agent/src/models/traffic.py
```

Current capabilities:

- captures TCP/UDP packets using Scapy
- extracts metadata only, not payloads
- excludes localhost, link-local, multicast, and broadcast traffic
- supports optional interface selection
- supports optional target IP filtering
- batches records every configured interval
- emergency flushes when the in-memory buffer reaches 50,000 records
- outputs captured records to stdout or a JSONL file
- handles graceful shutdown signals

Current record shape:

```json
{
  "timestamp": "2026-05-07T00:00:00Z",
  "src_ip": "192.168.1.10",
  "dst_ip": "192.168.1.20",
  "src_port": 51512,
  "dst_port": 443,
  "protocol": "TCP",
  "packet_size": 128,
  "tcp_flags": {
    "syn": false,
    "ack": true,
    "fin": false,
    "rst": false,
    "psh": true,
    "urg": false
  }
}
```

## Target Responsibilities

### 1. Endpoint Posture Collection

The agent should periodically collect endpoint posture information such as:

- hostname
- OS name/version
- local IP/MAC addresses
- uptime
- firewall status
- antivirus/security tool presence where possible
- patch/update status where possible
- disk encryption status where possible
- agent version and heartbeat timestamp

This posture data should be sent to the backend for compliance evaluation and dashboard visibility.

### 2. Network Traffic Capture

The agent should capture network metadata only:

- source IP
- destination IP
- source port
- destination port
- protocol
- packet size
- timestamp
- TCP flags

Payload content should not be captured.

The capture strategy should:

- filter TCP/UDP traffic only
- exclude localhost/link-local/broadcast/multicast traffic
- support interface selection
- support lab/simulation filtering by target IP
- require root/administrator privileges only where necessary

### 3. Traffic Batching

Captured traffic should be batched before processing/reporting.

Target behavior:

- batch interval: 60 seconds
- emergency flush threshold: 50,000 records
- avoid unbounded memory growth
- preserve graceful shutdown flushing

### 4. Feature Engineering

Per batch, the agent should convert packet metadata into model-ready features such as:

- packets per minute
- bytes per minute
- unique destination IP count
- unique destination port count
- average packet size
- TCP SYN/FIN/RST/ACK ratios
- well-known vs ephemeral port distribution
- connection fan-out indicators

### 5. Local Anomaly Detection

The target design is edge-based inference:

- load a pre-trained anomaly model locally
- run inference on engineered features
- compare anomaly score against configurable thresholds
- generate local alerts when suspicious behavior is detected

The PRD describes a pre-trained Isolation Forest model for detecting:

- brute-force attempts
- abnormal access frequency
- data exfiltration patterns
- port scanning behavior

Model files should eventually live under a path like:

```text
agent/src/ml/anomaly_model.joblib
```

### 6. Backend Reporting

The agent should report to the backend API:

```text
POST /api/posture
POST /api/traffic
POST /api/alerts
```

Expected behavior:

- authenticate agent requests
- retry safely on transient failures
- buffer locally when backend is unavailable
- avoid logging secrets/tokens/PII
- include agent/device identifiers in reports

### 7. Service Operation

The agent should eventually be installable as a managed service.

Linux target:

```text
systemd service
```

Windows target:

```text
Windows Service, preferably using NSSM/WinSW around a packaged executable for FYP practicality
```

A desktop tray app is optional and should not be responsible for core monitoring.

## Configuration

Settings are loaded from environment variables or `.env` using the `ZT_AGENT_` prefix.

Current settings include:

| Setting | Description | Default |
|---|---|---|
| `ZT_AGENT_INTERFACE` | Network interface to capture on | all interfaces |
| `ZT_AGENT_TARGET_IP` | Optional IP filter for lab/simulation traffic | none |
| `ZT_AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `ZT_AGENT_OUTPUT_MODE` | `stdout`, `file`, or `none` | `file` |
| `ZT_AGENT_OUTPUT_FILE` | Output path when using file mode | `./traffic.jsonl` |
| `ZT_AGENT_BATCH_INTERVAL` | Batch flush interval in seconds | `60` |

Example `.env`:

```env
ZT_AGENT_INTERFACE=eth0
ZT_AGENT_TARGET_IP=192.168.88.134
ZT_AGENT_LOG_LEVEL=INFO
ZT_AGENT_OUTPUT_MODE=file
ZT_AGENT_OUTPUT_FILE=./traffic.jsonl
ZT_AGENT_BATCH_INTERVAL=60
```

Do not commit real secrets in `.env`.

## Running Locally

Install dependencies:

```bash
cd agent
uv sync
```

Run the agent:

```bash
uv run python -m src.main
```

Packet capture usually requires elevated privileges:

```bash
sudo uv run python -m src.main
```

On Windows, packet capture may require Administrator privileges and Npcap.

## Future File Structure

The agent should evolve toward a structure like:

```text
agent/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── collectors/
│   │   ├── posture.py
│   │   └── traffic.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── buffer.py
│   │   ├── scheduler.py
│   │   ├── feature_engineering.py
│   │   └── alerting.py
│   ├── ml/
│   │   ├── inference.py
│   │   └── anomaly_model.joblib
│   └── models/
│       ├── posture.py
│       ├── traffic.py
│       └── alert.py
```

## Relationship to `/ids`

The `/ids` folder is currently a separate ML IDS training/inference workspace using flow-based CSV data and supervised classifiers such as Random Forest, XGBoost, and MLP.

The `/agent` folder is the runtime endpoint component. It should not be treated as just an experiment. It should become the deployable endpoint service that captures metadata, performs local detection, and reports to the backend.

If useful, trained artifacts or feature-engineering ideas from `/ids` can be adapted into `/agent`, but the PRD target for the agent is local anomaly detection using a pre-trained model.

## Security Notes

- Capture metadata only; do not capture packet payloads.
- Never log secrets, tokens, passwords, or unnecessary PII.
- Validate all outbound payloads with Pydantic models.
- Use least privilege where possible, even if packet capture requires elevated permissions.
- Prefer structured logs with request/trace identifiers.
- Use local buffering to avoid data loss during backend downtime.
