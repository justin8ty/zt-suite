"""Flow-based network monitoring pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from typing import TextIO
from uuid import uuid4

import pandas as pd

from src.config import settings
from src.ml.flow_classifier import FlowClassifier
from src.models.alert import AlertEnvelope, AlertRecord
from src.services.api_client import ApiClient
from src.services.cicflowmeter import CicFlowMeterError, pcap_to_flows
from src.services.identity import get_agent_id
from src.services.pcap_capture import capture_pcap_window


def run_flow_monitor(
    *,
    logger: Logger,
    flow_output_file: TextIO | None,
    alert_output_file: TextIO | None,
    api_client: ApiClient,
    shutdown_event,
) -> int:
    """Run PCAP-window -> CICFlowMeter -> IDS inference loop until shutdown."""
    classifier = FlowClassifier(logger=logger)
    if not classifier.available:
        logger.warning(
            "Flow classifier unavailable; captured CICFlowMeter rows will be "
            "written but not model-scored"
        )

    work_dir = Path(settings.flow_work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Starting flow-based monitoring: interval=%ss work_dir=%s",
        settings.flow_window_interval,
        work_dir,
    )

    while not shutdown_event.is_set():
        batch_id = str(uuid4())
        pcap_path = work_dir / f"{batch_id}.pcap"
        csv_path = work_dir / f"{batch_id}.csv"

        try:
            packet_count = capture_pcap_window(
                pcap_path,
                duration_seconds=settings.flow_window_interval,
                interface=settings.interface,
                logger=logger,
            )
        except PermissionError:
            logger.error(
                "Permission denied. Packet capture requires root/administrator. "
                "Run with: sudo uv run python -m src.main"
            )
            return 1
        except Exception as exc:  # noqa: BLE001 - top-level loop reports and exits.
            logger.exception("PCAP window capture failed: %s", exc)
            return 1

        if shutdown_event.is_set():
            break

        if packet_count == 0:
            logger.info("No packets captured for flow window batch_id=%s", batch_id)
            _cleanup_window_files(pcap_path, csv_path)
            continue

        try:
            flows = pcap_to_flows(pcap_path, csv_path, logger=logger)
        except CicFlowMeterError as exc:
            logger.warning("Skipping flow window; %s", exc)
            _cleanup_window_files(pcap_path, csv_path)
            continue

        if len(flows) == 0:
            logger.info("CICFlowMeter emitted no flows for batch_id=%s", batch_id)
            _cleanup_window_files(pcap_path, csv_path)
            continue

        try:
            scored = classifier.predict_with_metadata(flows)
        except Exception as exc:  # noqa: BLE001 - bad rows should not kill agent.
            logger.warning("Flow model scoring failed for batch_id=%s: %s", batch_id, exc)
            scored = flows.copy()
            scored["malicious_score"] = 0.0
            scored["prediction"] = 0
            scored["prediction_label"] = "ScoringFailed"

        _write_scored_flows(
            scored,
            batch_id=batch_id,
            flow_output_file=flow_output_file,
        )
        alert = _build_flow_alert(scored, batch_id=batch_id)
        if alert is not None:
            if alert_output_file is not None:
                alert_output_file.write(AlertEnvelope(alert=alert).model_dump_json() + "\n")
                alert_output_file.flush()
            api_client.report_alert(alert, source_ip=_top_source_ip(scored))
            logger.warning(
                "Flow IDS alert generated: alert_id=%s batch_id=%s score=%.3f",
                alert.alert_id,
                batch_id,
                alert.anomaly_score,
            )

        logger.info(
            "Processed flow window batch_id=%s packets=%s flows=%s max_score=%.3f malicious=%s",
            batch_id,
            packet_count,
            len(scored),
            _max_score(scored),
            int(scored.get("prediction", pd.Series(dtype=int)).sum()),
        )
        _cleanup_window_files(pcap_path, csv_path)

    logger.info("Flow-based monitoring stopped")
    return 0


def _write_scored_flows(
    scored: pd.DataFrame,
    *,
    batch_id: str,
    flow_output_file: TextIO | None,
) -> None:
    if settings.output_mode == "none":
        return

    envelope = {
        "type": "flow_features",
        "agent_id": get_agent_id(),
        "batch_id": batch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "flow_count": int(len(scored)),
        "flows": json.loads(scored.to_json(orient="records", date_format="iso")),
    }
    line = json.dumps(envelope, separators=(",", ":"))
    if settings.output_mode == "stdout":
        print(line, flush=True)
    elif settings.output_mode == "file" and flow_output_file is not None:
        flow_output_file.write(line + "\n")
        flow_output_file.flush()


def _build_flow_alert(scored: pd.DataFrame, *, batch_id: str) -> AlertRecord | None:
    if "malicious_score" not in scored.columns or len(scored) == 0:
        return None

    max_score = _max_score(scored)
    malicious_count = int(scored.get("prediction", pd.Series(dtype=int)).sum())
    if max_score < settings.flow_prediction_threshold and malicious_count == 0:
        return None

    return AlertRecord(
        alert_id=str(uuid4()),
        agent_id=get_agent_id(),
        batch_id=batch_id,
        created_at=datetime.now(timezone.utc),
        severity=_severity_from_score(max_score),
        confidence=max_score,
        anomaly_score=max_score,
        reason_codes=["flow_model_prediction"],
        message=f"Flow-based IDS detected {malicious_count} malicious flow(s)",
    )


def _max_score(scored: pd.DataFrame) -> float:
    if "malicious_score" not in scored.columns or len(scored) == 0:
        return 0.0
    return float(pd.to_numeric(scored["malicious_score"], errors="coerce").fillna(0).max())


def _top_source_ip(scored: pd.DataFrame) -> str | None:
    if "src_ip" not in scored.columns or len(scored) == 0:
        return None
    counts = scored["src_ip"].dropna().astype(str).value_counts()
    if len(counts) == 0:
        return None
    return str(counts.index[0])


def _severity_from_score(score: float) -> str:
    if score >= 0.9:
        return "critical"
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _cleanup_window_files(*paths: Path) -> None:
    if settings.flow_keep_artifacts:
        return
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
