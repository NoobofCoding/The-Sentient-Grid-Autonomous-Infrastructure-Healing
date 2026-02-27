"""Convenience entrypoint for the Pillar 3 Kafka consumer.

Usage (from repo root):
  python -m kafka_consumer

This delegates to intelligence.kafka_consumer.main().
"""

from __future__ import annotations


def main() -> None:
    from intelligence.kafka_consumer import main as consumer_main

    consumer_main()


if __name__ == "__main__":
    main()
