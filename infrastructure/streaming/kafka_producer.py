"""
Kafka producer for streaming grid state data from digital twin.

Publishes grid state snapshots to Kafka topics with comprehensive
error handling, delivery confirmation, and monitoring capabilities.

Note:
- Added `# -*- coding: utf-8 -*-` header for Windows/PowerShell UTF-8 support.
- Inserts project root into `sys.path` when run as script to ensure the
  `shared` module can be imported from anywhere (especially from CLI tools).
"""

# ensure imports work when this module is executed as a script
import os
import sys
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    # prepend so that local package modules (e.g., `shared`) take priority
    sys.path.insert(0, _ROOT)

# Add root of project to path to ensure `shared` package is importable when
# modules are executed directly (e.g., via scripts or during development).
import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import json
import logging
from typing import Optional, Dict, Any, Callable

from kafka import KafkaProducer
from kafka.errors import KafkaError

from shared.topic_names import GRID_STATE_TOPIC

logger = logging.getLogger(__name__)


class GridKafkaProducer:
    """
    Publishes grid state data to Kafka broker.

    Handles JSON serialization, error handling, and delivery callbacks.
    Provides metrics for monitoring message delivery success rates.

    Attributes:
        producer (KafkaProducer): Underlying Kafka producer instance.
        bootstrap_servers (str): Comma-separated list of broker addresses.
        messages_sent (int): Total messages successfully sent.
        messages_failed (int): Total messages that failed to send.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        acks: str = "all",
        retries: int = 3,
        compression_type: str = "gzip",
    ):
        """
        Initialize Kafka producer for grid state publishing.

        Args:
            bootstrap_servers (str): Kafka broker connection string.
            acks (str): Acknowledgment level ("0", "1", or "all").
            retries (int): Number of retry attempts for failed sends.
            compression_type (str): Compression type ("gzip", "snappy", "lz4").

        Raises:
            Exception: If producer initialization fails.
        """
        try:
            self.bootstrap_servers = bootstrap_servers
            self.messages_sent = 0
            self.messages_failed = 0

            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                acks=acks,
                retries=retries,
                compression_type=compression_type,
                value_serializer=self._serialize_state,
                request_timeout_ms=10000,
                connections_max_idle_ms=600000,
            )

            logger.info(
                f"GridKafkaProducer initialized: brokers={bootstrap_servers}, "
                f"compression={compression_type}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize KafkaProducer: {e}")
            raise

    def _serialize_state(self, state_data: Dict[str, Any]) -> bytes:
        """
        Serialize grid state to JSON bytes.

        Args:
            state_data (Dict[str, Any]): Grid state dictionary.

        Returns:
            bytes: JSON-encoded state data.

        Raises:
            TypeError: If state_data contains non-serializable objects.
        """
        try:
            return json.dumps(state_data).encode("utf-8")
        except TypeError as e:
            logger.error(f"Failed to serialize state: {e}")
            raise

    def _delivery_callback(
        self, message_metadata: Any, exception: Optional[Exception] = None
    ) -> None:
        """
        Handle Kafka delivery confirmation callback.

        Called after broker acknowledges message delivery (or failure).
        Updates metrics and logs results.

        Args:
            message_metadata: Kafka RecordMetadata with delivery info.
            exception (Optional[Exception]): Exception if delivery failed.
        """
        if exception is not None:
            self.messages_failed += 1
            # topic/partition/offset are attributes on RecordMetadata, not methods
            logger.error(
                f"Message delivery failed to {message_metadata.topic} "
                f"partition {message_metadata.partition}: {exception}"
            )
        else:
            self.messages_sent += 1
            logger.debug(
                f"Message delivered to {message_metadata.topic} "
                f"[{message_metadata.partition}] at offset {message_metadata.offset}"
            )

    def publish_state(
        self,
        state_dict: Dict[str, Any],
        topic: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Publish grid state to Kafka.

        Sends state asynchronously with optional custom callback.
        Default callback logs delivery status.

        Args:
            state_dict (Dict[str, Any]): Grid state dictionary from GridState.to_dict().
            topic (Optional[str]): Target topic. Defaults to GRID_STATE_TOPIC.
            callback (Optional[Callable]): Custom delivery callback.
                                         If None, uses _delivery_callback.

        Raises:
            ValueError: If state_dict is None or invalid.
            KafkaError: If producer is closed or broker unavailable.
        """
        if state_dict is None:
            raise ValueError("state_dict cannot be None")

        if topic is None:
            topic = GRID_STATE_TOPIC

        try:
            # Use custom callback if provided, otherwise use default
            cb = callback if callback is not None else self._delivery_callback

            future = self.producer.send(topic, value=state_dict)
            # ensure callback is callable to avoid sending a string by mistake
            if not callable(cb):
                logger.error(f"Provided callback of type {type(cb)} is not callable")
                raise TypeError("callback must be a callable")

            future.add_callback(cb)
            future.add_errback(self._error_callback)
            logger.debug(
                f"Published state at t={state_dict.get('timestamp', 'unknown')} "
                f"to topic '{topic}'"
            )

        except Exception as e:
            self.messages_failed += 1
            logger.error(f"Failed to publish state: {e}")
            raise

    def _error_callback(self, exc: Exception) -> None:
        """
        Handle Kafka errors that occur during async send.

        Args:
            exc (Exception): The exception that occurred.
        """
        logger.error(f"Kafka error callback triggered: {exc}")
        self.messages_failed += 1

    def flush(self, timeout_ms: Optional[int] = None) -> None:
        """
        Wait for all pending messages to be delivered.

        Blocks until all messages in the producer queue are sent
        or timeout expires.

        Args:
            timeout_ms (Optional[int]): Timeout in milliseconds.
                                       If None, waits indefinitely.
        """
        try:
            self.producer.flush(timeout_ms)
            logger.info("Producer flush completed")
        except KafkaError as e:
            logger.error(f"Error during producer flush: {e}")
            raise

    def close(self, timeout_ms: int = 30000) -> None:
        """
        Close the Kafka producer and clean up resources.

        Args:
            timeout_ms (int): Time to wait for pending sends before closing.
        """
        try:
            self.producer.close(timeout_ms)
            logger.info(
                f"GridKafkaProducer closed. Stats: "
                f"sent={self.messages_sent}, failed={self.messages_failed}"
            )
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get producer metrics and statistics.

        Returns:
            Dict[str, Any]: Message delivery metrics.
        """
        total = self.messages_sent + self.messages_failed
        success_rate = (
            (self.messages_sent / total * 100) if total > 0 else 0.0
        )

        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "total_messages": total,
            "success_rate_percent": success_rate,
        }