"""
Manager that handles periodic publishing of grid state to Kafka and/or MQTT.

Consumers of this class can supply their own producer implementations or rely
on the defaults from the streaming package.  The manager is configured via
`stream_config` and logs its progress for monitoring.
"""

import logging
import time
from typing import Optional

from . import stream_config

# Producers are imported lazily to avoid unnecessary dependencies for clients
from .kafka_producer import GridKafkaProducer
from .mqtt_producer import MqttGridProducer

logger = logging.getLogger(__name__)


class StreamManager:
    """Periodic publisher for grid state streams."""

    def __init__(
        self,
        use_kafka: bool = True,
        use_mqtt: bool = False,
        kafka_servers: Optional[str] = None,
        mqtt_broker: Optional[str] = None,
    ):
        self.use_kafka = use_kafka
        self.use_mqtt = use_mqtt
        self.kafka_producer: Optional[GridKafkaProducer] = None
        self.mqtt_producer: Optional[MqttGridProducer] = None

        if use_kafka:
            brokers = kafka_servers or stream_config.KAFKA_BOOTSTRAP_SERVERS
            self.kafka_producer = GridKafkaProducer(bootstrap_servers=brokers)

        if use_mqtt:
            broker = mqtt_broker or stream_config.MQTT_BROKER
            self.mqtt_producer = MqttGridProducer(broker=broker, port=stream_config.MQTT_PORT, topic=stream_config.MQTT_TOPIC)

    def publish(self, state: dict) -> None:
        """Send a single grid state to configured transports."""
        if self.kafka_producer:
            try:
                self.kafka_producer.publish_state(state)
            except Exception as e:
                logger.error(f"Kafka publish error: {e}")

        if self.mqtt_producer:
            try:
                self.mqtt_producer.publish_state(state)
            except Exception as e:
                logger.error(f"MQTT publish error: {e}")

    def run(self, env, steps: int = 0) -> None:
        """Run the stream loop.

        Args:
            env: GridEnvironment-like object with a `.step()` method returning
                 a state dictionary.
            steps: Number of steps to execute (0 for infinite).
        """
        count = 0
        try:
            while True:
                state = env.step()
                # ensure we have a dictionary
                if hasattr(state, "to_dict"):
                    msg = state.to_dict()
                else:
                    msg = state
                self.publish(msg)

                count += 1
                if steps and count >= steps:
                    break

                time.sleep(stream_config.STREAM_INTERVAL_SEC)
        except KeyboardInterrupt:
            logger.info("Streaming interrupted by user")
        finally:
            self.close()

    def close(self) -> None:
        """Clean up producer resources."""
        if self.kafka_producer:
            try:
                self.kafka_producer.flush()
                self.kafka_producer.close()
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
        if self.mqtt_producer:
            try:
                self.mqtt_producer.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MQTT producer: {e}")


# ---------------------------------------------------------------------------
# CLI entrypoint so users can run the manager directly with `python -m`
# ---------------------------------------------------------------------------

def main():
    """Command‑line interface for the StreamManager."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Sentient-Grid streaming manager (Kafka/MQTT)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Number of steps to execute (0 = infinite)"
    )
    parser.add_argument(
        "--no-kafka",
        action="store_true",
        help="Disable Kafka publishing"
    )
    parser.add_argument(
        "--mqtt",
        action="store_true",
        help="Enable MQTT publishing (requires paho-mqtt)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic environment"
    )
    parser.add_argument(
        "--faulty",
        action="store_true",
        help="Enable automatic faults in the environment"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    env = None
    try:
        from infrastructure.digital_twin.grid_env import GridEnvironment

        env = GridEnvironment(auto_fault=args.faulty, random_seed=args.seed)
    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}")
        sys.exit(1)

    manager = StreamManager(
        use_kafka=not args.no_kafka,
        use_mqtt=args.mqtt,
    )

    logger.info("Starting stream manager loop")
    manager.run(env, steps=args.steps)


if __name__ == "__main__":
    main()
