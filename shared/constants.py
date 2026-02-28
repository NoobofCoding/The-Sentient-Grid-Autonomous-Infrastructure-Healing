"""
Shared constants for inter-service contracts and runtime connectivity.
"""

from __future__ import annotations

import os


KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
"""Kafka bootstrap server list (comma-separated host:port entries)."""

CONTRACT_VERSION: str = os.getenv("CONTRACT_VERSION", "1.0.0")
"""Version tag for cross-service message and action contracts."""

