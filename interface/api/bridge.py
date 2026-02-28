"""
Lightweight API bridge exposing latest autonomous pipeline state.
"""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

LOGGER = logging.getLogger("interface.api.bridge")


class DashboardStateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current_state: Dict[str, Any] = {
            "status": "initializing",
            "message": "No state received yet",
        }

    def update(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._current_state = dict(payload)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._current_state)


def create_bridge_server(host: str, port: int, state_store: DashboardStateStore) -> ThreadingHTTPServer:
    class BridgeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
            if self.path != "/current_state":
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not_found"}')
                return

            payload = state_store.snapshot()
            body = json.dumps(payload).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:
            LOGGER.debug("Bridge HTTP: " + fmt, *args)

    return ThreadingHTTPServer((host, port), BridgeHandler)
