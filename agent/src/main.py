"""ZT Suite Traffic Capture Agent entry point."""

import json
import logging
import signal
import sys
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock, Timer
from typing import Callable, Final, TextIO

from src.collectors.posture import PostureCollector
from src.collectors.traffic import TrafficCollector
from src.config import settings
from src.models.posture import PostureEnvelope
from src.models.traffic import TrafficRecord

# Buffer size limits
BATCH_SIZE_SOFT_LIMIT: Final[int] = 50_000  # Emergency flush trigger
BATCH_SIZE_HARD_LIMIT: Final[int] = 100_000  # Safety net (should never hit)

# Shutdown event for graceful termination
_shutdown_event = Event()

# Batch buffer and timer
_record_buffer: Queue[TrafficRecord] = Queue()
_flush_timer: Timer | None = None
_posture_timer: Timer | None = None
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
        logger.info(f"Flushing {len(batch)} records ({flush_type})")

        # Output batch as JSON array
        batch_json = [record.model_dump(mode="json") for record in batch]
        json_output = json.dumps(batch_json)

        if settings.output_mode == "stdout":
            print(json_output, flush=True)
        elif settings.output_mode == "file" and output_file is not None:
            output_file.write(json_output + "\n")
            output_file.flush()


def _start_flush_timer(
    logger: logging.Logger,
    output_file: TextIO | None,
) -> None:
    """Start recurring timer to flush batch at configured interval."""
    global _flush_timer

    def flush_and_reschedule() -> None:
        global _flush_timer

        _flush_batch(logger, output_file, emergency=False)

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

        if settings.output_mode == "stdout":
            print(json_output, flush=True)
        elif settings.output_mode == "file" and posture_output_file is not None:
            posture_output_file.write(json_output + "\n")
            posture_output_file.flush()

        logger.info("Posture report collected for agent_id=%s", report.agent_id)


def _start_posture_timer(
    logger: logging.Logger,
    posture_output_file: TextIO | None,
) -> None:
    """Start recurring timer to collect endpoint posture."""
    global _posture_timer

    if not settings.posture_enabled:
        logger.info("Posture collection disabled")
        return

    collector = PostureCollector(logger=logger)

    def collect_and_reschedule() -> None:
        global _posture_timer

        _write_posture_report(logger, collector, posture_output_file)

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
) -> Callable[[TrafficRecord], None]:
    """Create callback that buffers records for batching."""

    def handle_record(record: TrafficRecord) -> None:
        _record_buffer.put(record)

        if _record_buffer.qsize() == 1:
            logger.info("First traffic record captured; waiting for batch flush")

        # Emergency flush if buffer too large
        if _record_buffer.qsize() >= BATCH_SIZE_SOFT_LIMIT:
            logger.warning(
                f"Buffer at {_record_buffer.qsize()} records, emergency flush triggered"
            )
            _flush_batch(logger, output_file, emergency=True)

    return handle_record


def _signal_handler(signum: int, frame: object) -> None:
    """Handle shutdown signals."""
    _shutdown_event.set()


def main() -> int:
    """Main entry point for the traffic capture agent."""
    global _flush_timer, _posture_timer

    logger = _setup_logging()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Validate configuration
    if settings.output_mode == "file" and not settings.output_file:
        logger.error("OUTPUT_FILE must be set when OUTPUT_MODE=file")
        return 1

    # Open output files if needed
    output_file: TextIO | None = None
    posture_output_file: TextIO | None = None
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

    try:
        # Start periodic timers
        _start_flush_timer(logger, output_file)
        _start_posture_timer(logger, posture_output_file)

        # Create and start collector
        collector = TrafficCollector(logger=logger)
        record_handler = _create_record_handler(logger, output_file)

        logger.info(
            f"Starting traffic capture on interface: "
            f"{settings.interface or 'all interfaces'}"
        )

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

        # Final flush of remaining records
        _flush_batch(logger, output_file, emergency=False)

        return 0

    finally:
        if output_file is not None:
            output_file.close()
        if posture_output_file is not None:
            posture_output_file.close()


if __name__ == "__main__":
    sys.exit(main())
