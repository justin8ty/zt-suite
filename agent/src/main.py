"""ZT Suite Traffic Capture Agent entry point."""

import json
import logging
import signal
import sys
from queue import Empty, Queue
from threading import Event, Lock, Timer
from typing import Callable, Final, TextIO

from src.collectors.traffic import TrafficCollector
from src.config import settings
from src.models.traffic import TrafficRecord

# Buffer size limits
BATCH_SIZE_SOFT_LIMIT: Final[int] = 50_000  # Emergency flush trigger
BATCH_SIZE_HARD_LIMIT: Final[int] = 100_000  # Safety net (should never hit)

# Shutdown event for graceful termination
_shutdown_event = Event()

# Batch buffer and timer
_record_buffer: Queue[TrafficRecord] = Queue()
_flush_timer: Timer | None = None
_flush_lock = Lock()


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
        batch_json = [record.model_dump() for record in batch]
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


def _create_record_handler(
    logger: logging.Logger,
    output_file: TextIO | None,
) -> Callable[[TrafficRecord], None]:
    """Create callback that buffers records for batching."""

    def handle_record(record: TrafficRecord) -> None:
        _record_buffer.put(record)

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
    global _flush_timer

    logger = _setup_logging()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Validate configuration
    if settings.output_mode == "file" and not settings.output_file:
        logger.error("OUTPUT_FILE must be set when OUTPUT_MODE=file")
        return 1

    # Open output file if needed
    output_file: TextIO | None = None
    if settings.output_mode == "file" and settings.output_file:
        try:
            output_file = open(settings.output_file, "a", encoding="utf-8")
            logger.info(f"Writing traffic records to {settings.output_file}")
        except OSError as e:
            logger.error(f"Failed to open output file: {e}")
            return 1

    try:
        # Start batch flush timer
        _start_flush_timer(logger, output_file)

        # Create and start collector
        collector = TrafficCollector()
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

        # Stop flush timer
        if _flush_timer is not None:
            _flush_timer.cancel()

        # Final flush of remaining records
        _flush_batch(logger, output_file, emergency=False)

        return 0

    finally:
        if output_file is not None:
            output_file.close()


if __name__ == "__main__":
    sys.exit(main())
