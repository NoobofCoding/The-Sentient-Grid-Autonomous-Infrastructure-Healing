"""
Debug utility to validate live observation feature construction from Kafka.

Consumes one message from grid.state.stream, builds observation vector,
prints shape and first 5 values, then exits.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from kafka import KafkaConsumer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from control_ai.observation_builder import build_observation_from_state
from shared.constants import KAFKA_BOOTSTRAP_SERVERS
from shared.topic_names import GRID_STATE_TOPIC


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    consumer = KafkaConsumer(
        GRID_STATE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=None,
        consumer_timeout_ms=10_000,
    )

    try:
        message = next(consumer)
        state_dict = message.value
        observation = build_observation_from_state(state_dict)

        print(f"Observation shape: {observation.shape}")
        print(f"First 5 values: {observation[:5].tolist()}")
    except StopIteration:
        print("No messages found on topic within timeout window.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
