"""
Lightweight MQTT producer for grid state messages.

This module depends on the `paho-mqtt` package but will behave gracefully if
it's not installed (Kafka fallback may still be used).  The class mirrors the
interface of `GridKafkaProducer` so callers can swap transport layers easily.
"""

import json
import logging
from typing import Optional, Dict, Any

try:
    import paho.mqtt.client as mqtt
except ImportError:  # type: ignore
    mqtt = None  # MQTT support optional

logger = logging.getLogger(__name__)


class MqttGridProducer:
    """Publishes grid state data over MQTT."""

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        topic: str = "grid/state",
        keepalive: int = 60,
    ):
        if mqtt is None:
            raise ImportError("paho-mqtt is required for MqttGridProducer but not installed")

        self.broker = broker
        self.port = port
        self.topic = topic
        self.keepalive = keepalive
        self.messages_sent = 0
        self.messages_failed = 0

        self.client = mqtt.Client()
        try:
            self.client.connect(broker, port, keepalive)
            logger.info(f"Connected to MQTT broker {broker}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def publish_state(self, state: Dict[str, Any]) -> None:
        """Publish state dictionary as JSON to configured topic."""
        if state is None:
            raise ValueError("state cannot be None")

        payload = json.dumps(state)
        try:
            result = self.client.publish(self.topic, payload)
            status = result[0] if isinstance(result, tuple) else result
            if status == mqtt.MQTT_ERR_SUCCESS:
                self.messages_sent += 1
                logger.debug(f"Published MQTT message to {self.topic}")
            else:
                self.messages_failed += 1
                logger.error(f"MQTT publish failed with status {status}")
        except Exception as e:
            self.messages_failed += 1
            logger.error(f"Exception during MQTT publish: {e}")
            raise

    def disconnect(self) -> None:
        try:
            self.client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")
