"""
Central configuration for streaming components.

Defines defaults for Kafka and MQTT endpoints, topic names, and the
interval at which grid state messages should be produced.
"""

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "10.150.2.151:9092"
KAFKA_TOPIC: str = "grid.state"

# MQTT configuration
MQTT_BROKER: str = "localhost"
MQTT_PORT: int = 1883
MQTT_TOPIC: str = "grid/state"

# General
STREAM_INTERVAL_SEC: float = 1.0
