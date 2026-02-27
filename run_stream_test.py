#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production-grade streaming integration test for sentient-grid digital twin.
"""

# add workspace root to path to support importing shared module from scripts
import os
import sys
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


import argparse
import logging
import sys
from datetime import datetime
from typing import Optional

from infrastructure.digital_twin.grid_env import GridEnvironment
from infrastructure.streaming.kafka_producer import GridKafkaProducer
from infrastructure.digital_twin.config import SIMULATION_STEP_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sentient_grid_stream_test.log"),
    ],
)

logger = logging.getLogger(__name__)


def run_streaming_test(
    num_steps: int = 20,
    random_seed: Optional[int] = None,
    auto_fault: bool = False,
    fault_interval: int = 5,
    bootstrap_servers: str = "localhost:9092",
    verbose: bool = False,
) -> dict:
    logger.info("=" * 80)
    logger.info("SENTIENT-GRID STREAMING TEST")
    logger.info("=" * 80)
    logger.info(f"Test Configuration:")
    logger.info(f"  Steps: {num_steps}")
    logger.info(f"  Random Seed: {random_seed}")
    logger.info(f"  Auto Faults: {auto_fault} (interval: {fault_interval})")
    logger.info(f"  Kafka Servers: {bootstrap_servers}")
    logger.info("")

    stats = {
        "start_time": datetime.now(),
        "num_steps": num_steps,
        "states_generated": 0,
        "states_published": 0,
        "states_faulted": 0,
        "producer_errors": 0,
        "messages_sent": 0,
        "messages_failed": 0,
    }

    try:
        # Initialize environment
        logger.info("Initializing GridEnvironment...")
        env = GridEnvironment(
            auto_fault=auto_fault,
            fault_interval=fault_interval,
            random_seed=random_seed,
        )
        logger.info("GridEnvironment initialized")

        # Initialize Kafka producer
        logger.info(f"Connecting to Kafka broker at {bootstrap_servers}...")
        try:
            producer = GridKafkaProducer(bootstrap_servers=bootstrap_servers)
            logger.info("KafkaProducer connected")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            logger.warning("Continuing without Kafka publishing...")
            producer = None

        logger.info("")
        logger.info("Starting simulation...")
        logger.info("-" * 80)

        # Run simulation
        for step in range(1, num_steps + 1):
            try:
                # Generate state
                state = env.step()
                stats["states_generated"] += 1

                # Track faults
                if state.is_faulted:
                    stats["states_faulted"] += 1

                # Publish to Kafka
                if producer:
                    try:
                        producer.publish_state(state.to_dict())
                        stats["states_published"] += 1
                    except Exception as e:
                        logger.error(f"Failed to publish state at t={state.timestamp}: {e}")
                        stats["producer_errors"] += 1
                else:
                    stats["states_published"] += 1

                # Format output
                fault_indicator = "FAULTED" if state.is_faulted else "NORMAL"
                frequency = f"{state.frequency:.2f}Hz"
                avg_voltage = sum(state.voltages) / len(state.voltages)
                avg_load = sum(state.loads) / len(state.loads)

                log_msg = (
                    f"Step {step:3d} | t={state.timestamp:6.1f}s | "
                    f"Freq={frequency:8s} | V_avg={avg_voltage:.3f}p.u. | "
                    f"Load_avg={avg_load:7.1f}MW | {fault_indicator}"
                )

                if verbose:
                    logger.info(log_msg)
                else:
                    # Use print for cleaner output in non-verbose mode
                    print(log_msg)

            except Exception as e:
                logger.error(f"Error at step {step}: {e}")
                raise

        logger.info("-" * 80)
        logger.info("")

        # Close producer
        if producer:
            logger.info("Flushing Kafka producer...")
            try:
                producer.flush()
                logger.info("Producer flushed")

                # Get metrics
                metrics = producer.get_metrics()
                stats["messages_sent"] = metrics["messages_sent"]
                stats["messages_failed"] = metrics["messages_failed"]

                logger.info("Closing Kafka producer...")
                producer.close()
                logger.info("Producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")

        stats["end_time"] = datetime.now()

        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {stats['end_time'] - stats['start_time']}")
        logger.info(f"States Generated: {stats['states_generated']}")
        logger.info(f"States Published: {stats['states_published']}")
        logger.info(f"States Faulted: {stats['states_faulted']}")

        if producer:
            logger.info(f"Kafka Messages Sent: {stats['messages_sent']}")
            logger.info(f"Kafka Messages Failed: {stats['messages_failed']}")
            if stats['messages_sent'] > 0:
                success_rate = (
                    stats['messages_sent'] / (stats['messages_sent'] + stats['messages_failed'])
                    * 100
                )
                logger.info(f"Success Rate: {success_rate:.1f}%")

        logger.info(f"Producer Errors: {stats['producer_errors']}")

        # Environment stats
        env_status = env.get_status()
        logger.info("")
        logger.info("Final Environment Status:")
        logger.info(f"  Timestamp: {env_status['timestamp']}")
        logger.info(f"  Total Load: {env_status['total_load']:.1f} MW")
        logger.info(f"  Total Generation: {env_status['total_generation']:.1f} MW")
        logger.info(f"  Imbalance: {env_status['total_load'] - env_status['total_generation']:.1f} MW")

        fault_status = env_status['fault_status']
        logger.info(f"  Fault Status: {'ACTIVE' if fault_status['has_active_fault'] else 'INACTIVE'}")
        if fault_status['has_active_fault']:
            logger.info(f"    Type: {fault_status['fault_type']}")
            logger.info(f"    Remaining Steps: {fault_status['remaining_steps']}")

        logger.info("=" * 80)
        logger.info(" TEST COMPLETED SUCCESSFULLY")
        logger.info("")

        return stats

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        stats["end_time"] = datetime.now()
        return stats

    except Exception as e:
        logger.error(f"Fatal error during test: {e}", exc_info=True)
        stats["end_time"] = datetime.now()
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Production-grade Kafka streaming test for sentient-grid digital twin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python script.py --steps 50 --faulty"
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=20,
        help="Number of simulation steps to execute (default: 20)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic simulation (default: non-deterministic)",
    )

    parser.add_argument(
        "--faulty",
        action="store_true",
        help="Enable automatic fault injection",
    )

    parser.add_argument(
        "--fault-interval",
        type=int,
        default=5,
        help="Steps between automatic faults (default: 5)",
    )

    parser.add_argument(
        "--bootstrap-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        stats = run_streaming_test(
            num_steps=args.steps,
            random_seed=args.seed,
            auto_fault=args.faulty,
            fault_interval=args.fault_interval,
            bootstrap_servers=args.bootstrap_servers,
            verbose=args.verbose,
        )

        # Exit with success code
        sys.exit(0)

    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()