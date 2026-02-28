"""Pillar 1 backend: local in-process state stream (no Kafka/MQTT)."""

from __future__ import annotations

import logging
import threading
import time
from queue import Queue
from typing import Any, Dict

from infrastructure.digital_twin.grid_env import GridEnvironment

LOGGER = logging.getLogger("stream_backend")


class LocalStateStream:
    """Continuously generate grid states and push them into an in-memory queue."""

    def __init__(self, state_queue: Queue[Dict[str, Any]], tick_seconds: float = 0.2) -> None:
        self.state_queue = state_queue
        self.tick_seconds = tick_seconds
        self.env = GridEnvironment(auto_fault=True, fault_interval=25)

    def run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            state_obj = self.env.step()
            payload = state_obj.to_dict()
            self.state_queue.put(payload)
            time.sleep(self.tick_seconds)
