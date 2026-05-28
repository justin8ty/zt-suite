"""ZT Suite Traffic Capture Agent entry point."""

import logging
import platform
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock, Timer
from typing import Callable, TextIO
from uuid import uuid4

from src.collectors.posture import PostureCollector
from src.collectors.traffic import TrafficCollector
from src.config import settings
from src.ml.inference import AnomalyDetector
from src.models.alert import AlertEnvelope
from src.models.features import TrafficFeatureEnvelope
from src.models.posture import PostureEnvelope
from src.models.traffic import TrafficBatchEnvelope, TrafficRecord
from src.services.api_client import ApiClient
from src.services.feature_engineering import build_features
from src.services.identity import get_agent_id

# Shutdown event for graceful termination
_shutdown_event = Event()

# Batch buffer and timer
_record_buffer: Queue[TrafficRecord] = Queue()
_flush_timer: Timer | None = None
_posture_timer: Timer | None = None
_capture_stats_timer: Timer | None = None
_flush_lock = Lock()
_posture_lock = Lock()


def _setup_logging() -> logging.Logger:
    """Configure logging to stderr."""
    logger = logging.getLogger("zt-agent")
    logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(settings.log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def _flush_batch(
    logger: logging.Logger,
    output_file: TextIO | None,
    feature_output_file: TextIO | None,
    alert_output_file: TextIO | None,
    anomaly_detector: AnomalyDetector,
    api_client: ApiClient,
    emergency: bool = False,
) -> None:
    """Flush accumulated records to output.

    Args:
        logger: Logger instance
        output_file: File handle for output (if mode=file)
        emergency: True if triggered by buffer overflow
    """
    with _flush_lock:  # Prevent concurrent flushes
        # Collect all buffered records
        batch = []
        while not _record_buffer.empty():
            try:
                batch.append(_record_buffer.get_nowait())
            except Empty:
                break

        if not batch:
            return  # Nothing to flush (silent)

        # Log flush
        flush_type = "emergency" if emergency else "scheduled"
        batch_id = str(uuid4())
        logger.info(
            "Flushing %s records (%s), batch_id=%s",
            len(batch),
            flush_type,
            batch_id,
        )

        agent_id = get_agent_id()
        envelope = TrafficBatchEnvelope(
            agent_id=agent_id,
            batch_id=batch_id,
            record_count=len(batch),
            flushed_at=datetime.now(timezone.utc),
            emergency=emergency,
            records=batch,
        )
        features = build_features(batch, agent_id=agent_id, batch_id=batch_id)
        feature_envelope = TrafficFeatureEnvelope(features=features)
        anomaly_result = anomaly_detector.score(features)
        alert = anomaly_detector.build_alert(features, anomaly_result)
        alert_envelope = AlertEnvelope(alert=alert) if alert is not None else None

        api_client.report_traffic_batch(envelope)
        if alert is not None:
            api_client.report_alert(alert)

        json_output = envelope.model_dump_json()
        feature_json_output = feature_envelope.model_dump_json()
        alert_json_output = (
            alert_envelope.model_dump_json() if alert_envelope is not None else None
        )

        if settings.output_mode == "stdout":
            print(json_output, flush=True)
            print(feature_json_output, flush=True)
            if alert_json_output is not None:
                print(alert_json_output, flush=True)
        elif settings.output_mode == "file" and output_file is not None:
            output_file.write(json_output + "\n")
            output_file.flush()
            if feature_output_file is not None:
                feature_output_file.write(feature_json_output + "\n")
                feature_output_file.flush()
            if alert_output_file is not None and alert_json_output is not None:
                alert_output_file.write(alert_json_output + "\n")
                alert_output_file.flush()

        logger.info(
            "Engineered traffic features for batch_id=%s: packets=%s, bytes=%s, unique_dst_ips=%s, anomaly_score=%.3f, anomalous=%s",
            batch_id,
            feature_envelope.features.packet_count,
            feature_envelope.features.byte_count,
            feature_envelope.features.unique_dst_ip_count,
            anomaly_result.score,
            anomaly_result.anomalous,
        )
        if alert is not None:
            logger.warning(
                "Local anomaly alert generated: alert_id=%s, batch_id=%s, severity=%s, reasons=%s",
                alert.alert_id,
                batch_id,
                alert.severity,
                ",".join(alert.reason_codes),
            )


def _start_flush_timer(
    logger: logging.Logger,
    output_file: TextIO | None,
    feature_output_file: TextIO | None,
    alert_output_file: TextIO | None,
    anomaly_detector: AnomalyDetector,
    api_client: ApiClient,
) -> None:
    """Start recurring timer to flush batch at configured interval."""
    global _flush_timer

    def flush_and_reschedule() -> None:
        global _flush_timer

        _flush_batch(
            logger,
            output_file,
            feature_output_file,
            alert_output_file,
            anomaly_detector,
            api_client,
            emergency=False,
        )

        # Reschedule if not shutting down
        if not _shutdown_event.is_set():
            _flush_timer = Timer(settings.batch_interval, flush_and_reschedule)
            _flush_timer.daemon = True
            _flush_timer.start()

    # Start first timer
    _flush_timer = Timer(settings.batch_interval, flush_and_reschedule)
    _flush_timer.daemon = True
    _flush_timer.start()

    logger.info(f"Batch flush timer started (interval: {settings.batch_interval}s)")


def _write_posture_report(
    logger: logging.Logger,
    collector: PostureCollector,
    posture_output_file: TextIO | None,
    api_client: ApiClient,
) -> None:
    """Collect and output one endpoint posture report."""
    with _posture_lock:
        try:
            report = collector.collect()
        except Exception as exc:  # noqa: BLE001 - posture must not stop traffic capture.
            logger.warning("Posture collection failed: %s", exc)
            return

        envelope = PostureEnvelope(report=report)
        json_output = envelope.model_dump_json()
        api_client.report_posture(report)

        if settings.output_mode == "stdout":
            print(json_output, flush=True)
        elif settings.output_mode == "file" and posture_output_file is not None:
            posture_output_file.write(json_output + "\n")
            posture_output_file.flush()

        logger.info("Posture report collected for agent_id=%s", report.agent_id)


def _start_capture_stats_timer(
    logger: logging.Logger,
    collector: TrafficCollector,
) -> None:
    """Start recurring traffic capture diagnostic logs."""
    global _capture_stats_timer

    def log_and_reschedule() -> None:
        global _capture_stats_timer

        stats = collector.stats()
        logger.info(
            "Traffic capture stats: seen=%s, emitted=%s, buffer=%s, "
            "skipped_excluded_ip=%s, skipped_target_ip=%s, skipped_no_ip=%s, "
            "skipped_no_transport=%s, skipped_fragmented=%s",
            stats["seen_packets"],
            stats["emitted_records"],
            _record_buffer.qsize(),
            stats["skipped_excluded_ip"],
            stats["skipped_target_ip"],
            stats["skipped_no_ip"],
            stats["skipped_no_transport"],
            stats["skipped_fragmented"],
        )

        if not _shutdown_event.is_set():
            _capture_stats_timer = Timer(
                settings.capture_stats_interval, log_and_reschedule
            )
            _capture_stats_timer.daemon = True
            _capture_stats_timer.start()

    _capture_stats_timer = Timer(settings.capture_stats_interval, log_and_reschedule)
    _capture_stats_timer.daemon = True
    _capture_stats_timer.start()
    logger.info(
        "Capture stats timer started (interval: %ss)", settings.capture_stats_interval
    )


def _start_posture_timer(
    logger: logging.Logger,
    posture_output_file: TextIO | None,
    api_client: ApiClient,
) -> None:
    """Start recurring timer to collect endpoint posture."""
    global _posture_timer

    if not settings.posture_enabled:
        logger.info("Posture collection disabled")
        return

    collector = PostureCollector(logger=logger)

    def collect_and_reschedule() -> None:
        global _posture_timer

        _write_posture_report(logger, collector, posture_output_file, api_client)

        if not _shutdown_event.is_set():
            _posture_timer = Timer(settings.posture_interval, collect_and_reschedule)
            _posture_timer.daemon = True
            _posture_timer.start()

    # Collect once immediately, then repeat at configured interval.
    collect_and_reschedule()
    logger.info(
        f"Posture timer started (interval: {settings.posture_interval}s)"
    )


def _create_record_handler(
    logger: logging.Logger,
    output_file: TextIO | None,
    feature_output_file: TextIO | None,
    alert_output_file: TextIO | None,
    anomaly_detector: AnomalyDetector,
    api_client: ApiClient,
) -> Callable[[TrafficRecord], None]:
    """Create callback that buffers records for batching."""

    def handle_record(record: TrafficRecord) -> None:
        current_size = _record_buffer.qsize()
        if current_size >= settings.batch_size_hard_limit:
            logger.error(
                "Traffic buffer hard limit reached (%s); dropping newest record",
                settings.batch_size_hard_limit,
            )
            return

        _record_buffer.put(record)
        current_size = _record_buffer.qsize()

        if current_size == 1:
            logger.info("First traffic record captured; waiting for batch flush")

        # Emergency flush if buffer too large
        if current_size >= settings.batch_size_soft_limit:
            logger.warning(
                "Buffer at %s records, emergency flush triggered",
                current_size,
            )
            _flush_batch(
                logger,
                output_file,
                feature_output_file,
                alert_output_file,
                anomaly_detector,
                api_client,
                emergency=True,
            )

    return handle_record


def _signal_handler(signum: int, frame: object) -> None:
    """Handle shutdown signals."""
    _shutdown_event.set()


def main() -> int:
    """Main entry point for the traffic capture agent."""
    global _flush_timer, _posture_timer, _capture_stats_timer

    logger = _setup_logging()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Validate configuration
    if settings.output_mode == "file" and not settings.output_file:
        logger.error("OUTPUT_FILE must be set when OUTPUT_MODE=file")
        return 1

    if settings.target_ip:
        logger.warning(
            "ZT_AGENT_TARGET_IP is set to %s; traffic not matching this IP will be skipped",
            settings.target_ip,
        )

    if platform.system().lower() == "windows" and not settings.interface:
        logger.warning(
            "ZT_AGENT_INTERFACE is empty on Windows; if capture is empty, set it to "
            "one of the logged Scapy interface names and run as Administrator with Npcap installed"
        )

    # Open output files if needed
    output_file: TextIO | None = None
    posture_output_file: TextIO | None = None
    feature_output_file: TextIO | None = None
    alert_output_file: TextIO | None = None
    if settings.output_mode == "file" and settings.output_file:
        try:
            output_path = Path(settings.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_file = open(settings.output_file, "a", encoding="utf-8")
            logger.info(f"Writing traffic records to {settings.output_file}")
        except OSError as e:
            logger.error(f"Failed to open traffic output file: {e}")
            return 1

    if settings.output_mode == "file" and settings.posture_enabled:
        try:
            posture_output_path = Path(settings.posture_output_file)
            posture_output_path.parent.mkdir(parents=True, exist_ok=True)
            posture_output_file = open(
                settings.posture_output_file, "a", encoding="utf-8"
            )
            logger.info(f"Writing posture reports to {settings.posture_output_file}")
        except OSError as e:
            logger.error(f"Failed to open posture output file: {e}")
            if output_file is not None:
                output_file.close()
            return 1

    if settings.output_mode == "file":
        try:
            feature_output_path = Path(settings.feature_output_file)
            feature_output_path.parent.mkdir(parents=True, exist_ok=True)
            feature_output_file = open(
                settings.feature_output_file, "a", encoding="utf-8"
            )
            logger.info(f"Writing traffic features to {settings.feature_output_file}")
        except OSError as e:
            logger.error(f"Failed to open feature output file: {e}")
            if output_file is not None:
                output_file.close()
            if posture_output_file is not None:
                posture_output_file.close()
            return 1

        try:
            alert_output_path = Path(settings.alert_output_file)
            alert_output_path.parent.mkdir(parents=True, exist_ok=True)
            alert_output_file = open(settings.alert_output_file, "a", encoding="utf-8")
            logger.info(f"Writing local alerts to {settings.alert_output_file}")
        except OSError as e:
            logger.error(f"Failed to open alert output file: {e}")
            if output_file is not None:
                output_file.close()
            if posture_output_file is not None:
                posture_output_file.close()
            if feature_output_file is not None:
                feature_output_file.close()
            return 1

    anomaly_detector = AnomalyDetector(logger=logger)
    api_client = ApiClient(logger=logger)

    try:
        # Start periodic timers
        _start_flush_timer(
            logger,
            output_file,
            feature_output_file,
            alert_output_file,
            anomaly_detector,
            api_client,
        )
        _start_posture_timer(logger, posture_output_file, api_client)

        # Create and start collector
        collector = TrafficCollector(logger=logger)
        record_handler = _create_record_handler(
            logger,
            output_file,
            feature_output_file,
            alert_output_file,
            anomaly_detector,
            api_client,
        )

        logger.info(
            f"Starting traffic capture on interface: "
            f"{settings.interface or 'all interfaces'}"
        )

        _start_capture_stats_timer(logger, collector)

        try:
            collector.start(callback=record_handler, interface=settings.interface)
        except PermissionError:
            logger.error(
                "Permission denied. Packet capture requires root/administrator. "
                "Run with: sudo uv run python -m src.main"
            )
            return 1
        except OSError as e:
            logger.error(f"Failed to start capture: {e}")
            return 1

        logger.info("Traffic capture started. Press Ctrl+C to stop.")

        # Block until shutdown signal
        _shutdown_event.wait()

        logger.info("Shutting down...")
        collector.stop()
        logger.info("Traffic capture stopped.")

        # Stop timers
        if _flush_timer is not None:
            _flush_timer.cancel()
        if _posture_timer is not None:
            _posture_timer.cancel()
        if _capture_stats_timer is not None:
            _capture_stats_timer.cancel()

        # Final flush of remaining records
        _flush_batch(
            logger,
            output_file,
            feature_output_file,
            alert_output_file,
            anomaly_detector,
            api_client,
            emergency=False,
        )

        return 0

    finally:
        if output_file is not None:
            output_file.close()
        if posture_output_file is not None:
            posture_output_file.close()
        if feature_output_file is not None:
            feature_output_file.close()
        if alert_output_file is not None:
            alert_output_file.close()


if __name__ == "__main__":
    sys.exit(main())
