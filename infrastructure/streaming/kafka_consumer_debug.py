"""
Debug Kafka consumer for monitoring grid state messages in real-time.

Provides a simple CLI tool for consuming and displaying grid state
messages from Kafka topic in a human-readable format with validation.

Note:
- Added `# -*- coding: utf-8 -*-` header for Windows/PowerShell UTF-8 support.
- Prepend project root to sys.path when run directly so the `shared` package
  can be located (mirrors fix in other scripts).
"""

# ensure shared module can be resolved when running from this location
import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ensure shared module can be resolved when running from this location
import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import json
import logging
import sys
from typing import Optional, Dict, Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from shared.topic_names import GRID_STATE_TOPIC

logger = logging.getLogger(__name__)


class GridStateConsumerDebug:
    """
    Debug consumer for grid state message topic.

    Deserializes JSON messages and displays them in a structured,
    human-readable format. Validates message schema and logs errors.

    Attributes:
        consumer (KafkaConsumer): Underlying Kafka consumer.
        topic (str): Topic name being consumed.
        messages_received (int): Total messages received.
        messages_invalid (int): Total invalid/undeserializable messages.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = GRID_STATE_TOPIC,
        group_id: str = "grid-debug-consumer",
        auto_offset_reset: str = "earliest",
    ):
        """
        Initialize debug consumer for grid state messages.

        Args:
            bootstrap_servers (str): Kafka broker connection string.
            topic (str): Topic to consume from.
            group_id (str): Consumer group ID for offset management.
            auto_offset_reset (str): Offset reset policy ("earliest" or "latest").

        Raises:
            KafkaError: If consumer initialization fails.
        """
        try:
            self.topic = topic
            self.messages_received = 0
            self.messages_invalid = 0

            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000,
                session_timeout_ms=30000,
            )

            logger.info(
                f"GridStateConsumerDebug initialized: "
                f"brokers={bootstrap_servers}, topic={topic}, group={group_id}"
            )

        except KafkaError as e:
            logger.error(f"Failed to initialize KafkaConsumer: {e}")
            raise

    def validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate grid state message schema.

        Checks that message contains all required fields with correct types.

        Args:
            message (Dict[str, Any]): Message dictionary to validate.

        Returns:
            bool: True if message is valid, False otherwise.
        """
        required_fields = {
            "timestamp": (int, float),
            "voltages": list,
            "voltage_angles": list,
            "loads": list,
            "generator_outputs": list,
            "line_flows": list,
            "frequency": (int, float),
        }

        for field, expected_type in required_fields.items():
            if field not in message:
                logger.warning(f"Missing required field: {field}")
                return False

            if not isinstance(message[field], expected_type):
                logger.warning(
                    f"Field {field} has incorrect type: "
                    f"expected {expected_type}, got {type(message[field])}"
                )
                return False

        # Validate array dimensions
        try:
            if len(message["voltages"]) != 39:
                logger.warning(f"Invalid voltages array length: {len(message['voltages'])}")
                return False

            if len(message["generator_outputs"]) != 10:
                logger.warning(
                    f"Invalid generator_outputs array length: "
                    f"{len(message['generator_outputs'])}"
                )
                return False

            if len(message["line_flows"]) != 46:
                logger.warning(
                    f"Invalid line_flows array length: {len(message['line_flows'])}"
                )
                return False

        except (TypeError, AttributeError) as e:
            logger.warning(f"Error validating array dimensions: {e}")
            return False

        return True

    def format_message(self, message: Dict[str, Any]) -> str:
        """
        Format grid state message for display.

        Args:
            message (Dict[str, Any]): Grid state message dictionary.

        Returns:
            str: Formatted message string.
        """
        output = []

        # Header
        output.append(
            f"\n{'='*80}"
        )
        output.append(
            f"GRID STATE SNAPSHOT [t={message.get('timestamp', 'N/A')}s]"
        )
        output.append(f"{'='*80}")

        # Fault status (use ASCII symbols to avoid Windows console issues)
        if message.get("is_faulted", False):
            output.append(
                f"[FAULT] FAULT ACTIVE: {message.get('fault_info', {}).get('type', 'unknown')}"
            )

        # Frequency
        freq = message.get("frequency", 0.0)
        # replace unicode checkmark with ASCII indicator for Windows compatibility
        freq_status = "[OK] NORMAL" if 49.0 <= freq <= 51.0 else "[!UNSAFE] OUT-OF-BOUNDS"
        output.append(f"\nFREQUENCY: {freq:.3f} Hz [{freq_status}]")

        # Voltages
        voltages = message.get("voltages", [])
        if voltages:
            import statistics

            avg_v = statistics.mean(voltages)
            min_v = min(voltages)
            max_v = max(voltages)
            output.append(
                f"\nBUS VOLTAGES (p.u.):"
                f"\n  Average:  {avg_v:.4f}"
                f"\n  Min/Max:  {min_v:.4f} / {max_v:.4f}"
            )

        # Loads
        loads = message.get("loads", [])
        if loads:
            total_load = sum(loads)
            avg_load = total_load / len(loads) if loads else 0
            output.append(
                f"\nLOADS (MW):"
                f"\n  Total:    {total_load:.1f}"
                f"\n  Average:  {avg_load:.1f}"
            )

        # Generation
        gen = message.get("generator_outputs", [])
        if gen:
            total_gen = sum(gen)
            avg_gen = total_gen / len(gen) if gen else 0
            output.append(
                f"\nGENERATION (MW):"
                f"\n  Total:    {total_gen:.1f}"
                f"\n  Average:  {avg_gen:.1f}"
            )

        # Line Flows
        flows = message.get("line_flows", [])
        if flows:
            total_flow = sum(flows)
            avg_flow = total_flow / len(flows) if flows else 0
            output.append(
                f"\nTRANSMISSION LINE FLOWS (MW):"
                f"\n  Total:    {total_flow:.1f}"
                f"\n  Average:  {avg_flow:.1f}"
            )

        # Balance
        if loads and gen:
            imbalance = sum(loads) - sum(gen)
            output.append(f"\nLOAD-GENERATION IMBALANCE: {imbalance:.1f} MW")

        output.append(f"\n{'='*80}")

        return "\n".join(output)

    def consume_and_print(self, max_messages: Optional[int] = None) -> None:
        """
        Consume messages from topic and print in formatted manner.

        Args:
            max_messages (Optional[int]): Maximum messages to consume.
                                         If None, consume indefinitely.
        """
        try:
            logger.info(f"Consuming from topic '{self.topic}'...")
            print(f"\n[GridStateConsumerDebug] Listening to topic: {self.topic}")
            print(f"Press Ctrl+C to stop.\n")

            count = 0

            for message in self.consumer:
                try:
                    if message.value is None:
                        logger.warning("Received null message value")
                        self.messages_invalid += 1
                        continue

                    # Validate message schema
                    if not self.validate_message(message.value):
                        self.messages_invalid += 1
                        continue

                    # Format and print
                    formatted = self.format_message(message.value)
                    print(formatted)

                    self.messages_received += 1
                    count += 1

                    if max_messages and count >= max_messages:
                        break

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to deserialize message: {e}")
                    self.messages_invalid += 1
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.messages_invalid += 1

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
            print("\n\n[GridStateConsumerDebug] Interrupted by user")

        except KafkaError as e:
            logger.error(f"Kafka error during consumption: {e}")
            raise

        finally:
            self.close()

    def close(self) -> None:
        """Close the Kafka consumer."""
        try:
            self.consumer.close()
            print(
                f"\n[GridStateConsumerDebug] Consumer closed."
                f"\nStats: {self.messages_received} valid, {self.messages_invalid} invalid"
            )
            logger.info(
                f"Consumer closed. Stats: "
                f"received={self.messages_received}, invalid={self.messages_invalid}"
            )

        except Exception as e:
            logger.error(f"Error closing consumer: {e}")


def main():
    """CLI entry point for debug consumer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Debug consumer for grid state Kafka topic"
    )
    parser.add_argument(
        "--bootstrap-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default=GRID_STATE_TOPIC,
        help=f"Topic to consume from (default: {GRID_STATE_TOPIC})",
    )
    parser.add_argument(
        "--group",
        default="grid-debug-consumer",
        help="Consumer group ID (default: grid-debug-consumer)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help="Maximum messages to consume (default: unlimited)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run consumer
    consumer = GridStateConsumerDebug(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group,
    )

    consumer.consume_and_print(max_messages=args.max_messages)


if __name__ == "__main__":
    main()
