"""Local loopback identity endpoint for browser-to-agent device detection."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging import Logger
from threading import Thread
from typing import Any

from src.config import settings
from src.services.identity import get_agent_id


class LocalIdentityServer:
    """Small HTTP server bound to loopback for local browser device detection."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start the local identity endpoint in a background thread."""
        if not settings.local_identity_enabled:
            self._logger.info("Local identity endpoint disabled")
            return

        handler = _build_handler(self._logger)
        try:
            self._server = ThreadingHTTPServer(
                (settings.local_identity_host, settings.local_identity_port),
                handler,
            )
        except OSError as exc:
            self._logger.warning("Local identity endpoint unavailable: %s", exc)
            return

        self._thread = Thread(
            target=self._server.serve_forever,
            name="local-identity-server",
            daemon=True,
        )
        self._thread.start()
        self._logger.info(
            "Local identity endpoint listening on http://%s:%s",
            settings.local_identity_host,
            settings.local_identity_port,
        )

    def stop(self) -> None:
        """Stop the local identity endpoint."""
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None


def _build_handler(logger: Logger) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler API
            self._send_empty_response(204)

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            if self.path.split("?", 1)[0] != "/identity":
                self._send_json({"detail": "Not found"}, status=404)
                return

            payload: dict[str, Any] = {
                "agent_running": True,
                "agent_id": get_agent_id(),
                "device_id": settings.device_id,
            }
            self._send_json(payload)

        def log_message(self, format: str, *args: object) -> None:
            logger.debug("Local identity endpoint: " + format, *args)

        def _send_empty_response(self, status: int) -> None:
            self.send_response(status)
            self._send_cors_headers()
            self.end_headers()

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Cache-Control", "no-store")

    return Handler
