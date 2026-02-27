#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentient-Grid Streaming Backend

This is the main entry point for running the grid simulation and
streaming system as a continuous backend service. It will run indefinitely,
publishing grid state messages to Kafka and/or MQTT at a configurable interval.

Usage:
    python stream_backend.py                    # default (Kafka, infinite)
    python stream_backend.py --mqtt             # enable MQTT too
    python stream_backend.py --seed 42          # deterministic
    python stream_backend.py --faulty --mqtt    # faults + MQTT

To run as a Windows Task Scheduler background job:
    1. Open Task Scheduler
    2. Create Basic Task -> "Sentient-Grid Stream Backend"
    3. Trigger: At startup
    4. Action: C:\\path\\to\\python.exe stream_backend.py
    5. Advanced: Check "Run whether user is logged in"

To run as a background process in PowerShell:
    Start-Process python -ArgumentList @("stream_backend.py") -WindowStyle Hidden
    # or with output logging:
    Start -Process python -ArgumentList @("stream_backend.py") -RedirectStandardOut "stream.log"

To run in a Docker container:
    docker build -t sentient-grid .
    docker run -d --name grid-stream \
        -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
        sentient-grid python stream_backend.py
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add workspace root to path
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from infrastructure.digital_twin.grid_env import GridEnvironment
from infrastructure.streaming.stream_manager import StreamManager
from infrastructure.streaming import stream_config


def setup_logging(log_file: str = "sentient_grid_backend.log") -> logging.Logger:
    """Configure logging to both console and file."""
    logger = logging.getLogger("sentient-grid-backend")
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)

    # File handler (append mode, so logs persist across restarts)
    try:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler: {e}")

    logger.addHandler(console_handler)
    return logger


def main():
    """Main entry point for the backend."""
    parser = argparse.ArgumentParser(
        description="Sentient-Grid Streaming Backend (runs indefinitely)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Kafka transport, infinite loop
  python stream_backend.py

  # Enable MQTT in addition to Kafka
  python stream_backend.py --mqtt

  # Deterministic + automatic faults
  python stream_backend.py --seed 42 --faulty

  # Disable Kafka, use MQTT only
  python stream_backend.py --no-kafka --mqtt

  # Custom Kafka broker
  python stream_backend.py --kafka-servers broker1:9092,broker2:9092
        """,
    )

    parser.add_argument(
        "--no-kafka",
        action="store_true",
        help="Disable Kafka publishing",
    )
    parser.add_argument(
        "--mqtt",
        action="store_true",
        help="Enable MQTT publishing (requires paho-mqtt)",
    )
    parser.add_argument(
        "--kafka-servers",
        type=str,
        default=None,
        help=f"Kafka bootstrap servers (default: {stream_config.KAFKA_BOOTSTRAP_SERVERS})",
    )
    parser.add_argument(
        "--mqtt-broker",
        type=str,
        default=None,
        help=f"MQTT broker address (default: {stream_config.MQTT_BROKER})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic environment (default: non-deterministic)",
    )
    parser.add_argument(
        "--faulty",
        action="store_true",
        help="Enable automatic random fault injection",
    )
    parser.add_argument(
        "--fault-interval",
        type=int,
        default=20,
        help="Steps between automatic faults (default: 20)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="sentient_grid_backend.log",
        help="Log file path (default: sentient_grid_backend.log)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(log_file=args.log_file)

    logger.info("=" * 80)
    logger.info("SENTIENT-GRID STREAMING BACKEND STARTING")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Log file: {args.log_file}")
    logger.info(f"Kafka enabled: {not args.no_kafka}")
    logger.info(f"MQTT enabled: {args.mqtt}")
    logger.info(f"Deterministic seed: {args.seed}")
    logger.info(f"Auto-faults: {args.faulty}")
    logger.info("")

    # Initialize environment
    try:
        logger.info("Initializing GridEnvironment...")
        env = GridEnvironment(
            auto_fault=args.faulty,
            fault_interval=args.fault_interval,
            random_seed=args.seed,
        )
        logger.info("GridEnvironment initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}", exc_info=True)
        sys.exit(1)

    # Initialize stream manager
    try:
        logger.info("Initializing StreamManager...")
        manager = StreamManager(
            use_kafka=not args.no_kafka,
            use_mqtt=args.mqtt,
            kafka_servers=args.kafka_servers,
            mqtt_broker=args.mqtt_broker,
        )
        logger.info("StreamManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize StreamManager: {e}", exc_info=True)
        sys.exit(1)

    logger.info("")
    logger.info("=" * 80)
    logger.info("BACKEND RUNNING - Publishing grid state indefinitely")
    logger.info("Press Ctrl+C to stop gracefully")
    logger.info("=" * 80)
    logger.info("")

    # Run indefinitely (steps=0)
    try:
        manager.run(env, steps=0)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Backend shutdown complete")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
