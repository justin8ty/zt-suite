"""ZT Suite Traffic Capture Agent entry point."""

import logging
import signal
import sys
from threading import Event
from typing import TextIO

from src.collectors.traffic import TrafficCollector
from src.config import settings
from src.models.traffic import TrafficRecord

# Shutdown event for graceful termination
_shutdown_event = Event()


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


def _create_record_handler(
    logger: logging.Logger,
    output_file: TextIO | None,
) -> callable:
    """Create callback function for handling captured traffic records."""

    def handle_record(record: TrafficRecord) -> None:
        json_line = record.model_dump_json()

        if settings.output_mode == "stdout":
            print(json_line, flush=True)
        elif settings.output_mode == "file" and output_file is not None:
            output_file.write(json_line + "\n")
            output_file.flush()
        # output_mode == "none" -> do nothing

    return handle_record


def _signal_handler(signum: int, frame: object) -> None:
    """Handle shutdown signals."""
    _shutdown_event.set()


def main() -> int:
    """Main entry point for the traffic capture agent."""
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

        return 0

    finally:
        if output_file is not None:
            output_file.close()


if __name__ == "__main__":
    sys.exit(main())
