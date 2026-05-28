"""Backend API client for agent reporting."""

from __future__ import annotations

from logging import Logger

import httpx

from src.config import settings
from src.models.alert import AlertRecord
from src.models.posture import PostureReport
from src.models.traffic import TrafficBatchEnvelope, TrafficRecord


class ApiClient:
    """Small synchronous client for backend reporting."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger
        self._device_id = settings.device_id
        self._base_url = settings.backend_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return settings.reporting_enabled

    def report_posture(self, report: PostureReport) -> None:
        """Submit posture report for the configured backend device."""
        if not self._ready():
            return

        device_id = self._ensure_device_id(report)
        if device_id is None:
            return

        payload = {
            "antivirus_present": bool(report.security.antivirus_present),
            "antivirus_enabled": bool(report.security.antivirus_present),
            "firewall_enabled": bool(report.security.firewall_enabled),
            "disk_encrypted": bool(report.security.disk_encryption_enabled),
            "os_up_to_date": False if report.security.updates_available is None else not report.security.updates_available,
        }
        self._post(f"/api/devices/{device_id}/posture", payload, "posture report")

    def report_traffic_batch(self, batch: TrafficBatchEnvelope) -> None:
        """Submit traffic batch to backend."""
        if not self._ready():
            return

        device_id = self._device_id
        if device_id is None:
            self._warn("Skipping traffic report; no backend device_id available")
            return

        payload = {
            "device_id": device_id,
            "records": [_traffic_record_payload(record) for record in batch.records],
        }
        self._post("/api/traffic", payload, f"traffic batch {batch.batch_id}")

    def report_alert(self, alert: AlertRecord, source_ip: str | None = None) -> None:
        """Submit local alert to backend."""
        if not self._ready():
            return

        device_id = self._device_id
        if device_id is None:
            self._warn("Skipping alert report; no backend device_id available")
            return

        payload = {
            "device_id": device_id,
            "severity": alert.severity,
            "category": "network_anomaly",
            "title": "Endpoint anomaly detected",
            "description": f"{alert.message}; reasons={','.join(alert.reason_codes)}; score={alert.anomaly_score:.3f}",
            "source_ip": source_ip,
        }
        self._post("/api/alerts", payload, f"alert {alert.alert_id}")

    def _ensure_device_id(self, report: PostureReport) -> int | None:
        if self._device_id is not None:
            return self._device_id

        self._warn(
            "Skipping posture report for hostname=%s; ZT_AGENT_DEVICE_ID is required with agent-token authentication",
            report.hostname,
        )
        return None

    def _ready(self) -> bool:
        if not settings.reporting_enabled:
            return False
        if not settings.agent_token:
            self._warn("Backend reporting enabled but ZT_AGENT_TOKEN is missing")
            return False
        return True

    def _post(self, path: str, payload: dict[str, object], label: str) -> object | None:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {settings.agent_token}"}
        try:
            with httpx.Client(timeout=settings.api_timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._warn(
                "Backend %s failed: status=%s body=%s",
                label,
                exc.response.status_code,
                exc.response.text[:300],
            )
            return None
        except httpx.HTTPError as exc:
            self._warn("Backend %s failed: %s", label, exc)
            return None

        self._info("Backend %s sent successfully", label)
        if response.content:
            return response.json()
        return None

    def _warn(self, message: str, *args: object) -> None:
        if self._logger:
            self._logger.warning(message, *args)

    def _info(self, message: str, *args: object) -> None:
        if self._logger:
            self._logger.info(message, *args)


def _traffic_record_payload(record: TrafficRecord) -> dict[str, object]:
    return {
        "src_ip": record.src_ip,
        "dst_ip": record.dst_ip,
        "src_port": record.src_port,
        "dst_port": record.dst_port,
        "protocol": record.protocol,
        "bytes_sent": record.packet_size,
        "bytes_received": 0,
        "timestamp": record.timestamp.isoformat(),
    }
