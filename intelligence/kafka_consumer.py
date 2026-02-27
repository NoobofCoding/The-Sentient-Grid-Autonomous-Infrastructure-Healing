import json
import time
import importlib
import sys
import sysconfig
from pathlib import Path
from typing import Any


# Support running as a script: `python intelligence/kafka_consumer.py`
# Put the project root on sys.path so `import intelligence` works, and avoid
# the package directory shadowing stdlib modules (notably `logging`).
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    sys.path.remove(str(_script_dir))
except ValueError:
    pass


def _import_stdlib_logging():
    """Import stdlib `logging` even if a local `logging/` package shadows it.

    Running as `python intelligence/kafka_consumer.py` adds `intelligence/` to
    `sys.path` first, which makes `intelligence/logging/` shadow the stdlib
    `logging` module. Kafka (and many libs) depend on the stdlib module.
    """

    stdlib_path = sysconfig.get_paths().get("stdlib")
    if stdlib_path and stdlib_path not in sys.path:
        sys.path.insert(0, stdlib_path)

    sys.modules.pop("logging", None)
    logging_mod = importlib.import_module("logging")

    # Sanity check: stdlib logging has Handler.
    if not hasattr(logging_mod, "Handler") and stdlib_path:
        # Ensure stdlib wins import precedence.
        if sys.path[0] != stdlib_path:
            try:
                sys.path.remove(stdlib_path)
            except ValueError:
                pass
            sys.path.insert(0, stdlib_path)
        sys.modules.pop("logging", None)
        logging_mod = importlib.import_module("logging")

    sys.modules["logging"] = logging_mod
    return logging_mod


logging = _import_stdlib_logging()

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka import errors as kafka_errors
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Failed to import kafka-python. "
        "Install `kafka-python` in the same interpreter you're running, "
        "or run using the project venv: `& .venv/Scripts/python.exe -m kafka_consumer`. "
        "If you are using system Python, your installation may be corrupted (missing `kafka/__init__.py`)."
    ) from exc

from intelligence.anomaly_detection.detector_service import AnomalyDetectionService
from intelligence.logging.event_logger import EventLogger
from intelligence.safety.safety_filter import SafetyFilter

from shared.constants import (
    ANOMALY_SEVERITY_ALERT_THRESHOLD,
    ENABLE_KAFKA_OUTPUT_TOPICS,
    load_kafka_config,
)
from shared.schema_validation import SchemaValidationError, decode_and_validate_json
from shared.topic_names import (
    ANOMALY_DETECTION_TOPIC,
    GRID_STATE_ALERTS_TOPIC,
    GRID_STATE_TOPIC,
)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("intelligence.kafka_consumer")

    kafka_cfg = load_kafka_config()
    event_logger = EventLogger()
    safety_filter = SafetyFilter()

    detector: AnomalyDetectionService | None = None

    producer: KafkaProducer | None = None

    def _get_producer() -> KafkaProducer | None:
        nonlocal producer
        if not ENABLE_KAFKA_OUTPUT_TOPICS:
            return None
        if producer is not None:
            return producer

        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_cfg.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            return producer
        except kafka_errors.NoBrokersAvailable as exc:
            logger.warning("Kafka producer unavailable (%s). Output topics disabled for now.", exc)
            producer = None
            return None

    backoff_s = kafka_cfg.reconnect_backoff_initial_s

    while True:
        consumer: KafkaConsumer | None = None
        try:
            logger.info(
                "Connecting to Kafka at %s (topic=%s)",
                kafka_cfg.bootstrap_servers,
                GRID_STATE_TOPIC,
            )

            consumer = KafkaConsumer(
                GRID_STATE_TOPIC,
                bootstrap_servers=kafka_cfg.bootstrap_servers,
                auto_offset_reset=kafka_cfg.auto_offset_reset,
                enable_auto_commit=kafka_cfg.enable_auto_commit,
                group_id=kafka_cfg.group_id,
                client_id=kafka_cfg.client_id,
                # Fail faster when broker is unreachable; we'll retry with backoff.
                api_version_auto_timeout_ms=3000,
                # kafka-python requires request_timeout_ms > session_timeout_ms
                session_timeout_ms=10000,
                heartbeat_interval_ms=3000,
                request_timeout_ms=30000,
            )

            logger.info("Connected. Waiting for GridState messages...")
            backoff_s = kafka_cfg.reconnect_backoff_initial_s

            while True:
                records = consumer.poll(
                    timeout_ms=kafka_cfg.poll_timeout_ms,
                    max_records=kafka_cfg.max_records_per_poll,
                )
                if not records:
                    continue

                for _tp, messages in records.items():
                    for msg in messages:
                        payload = msg.value
                        if payload is None:
                            continue

                        try:
                            state: dict[str, Any] = decode_and_validate_json(payload)
                        except SchemaValidationError as exc:
                            logger.error("Dropping invalid message: %s", exc)
                            continue

                        # Initialize detector with feature count matching feature_engineering.py
                        if detector is None:
                            feature_count = (
                                len(state["voltages"]) + len(state["loads"]) + 1
                            )
                            detector = AnomalyDetectionService(input_dim=feature_count)
                            logger.info(
                                "Detector initialized with input_dim=%s", feature_count
                            )

                        result = detector.process(state)
                        severity = float(result["severity_score"])

                        # Run safety filter (uses frequency bounds; falls back if unsafe)
                        proposed_action = {
                            "action_id": 0,
                            "target_bus": None,
                            "load_reduction_percent": 0.0,
                        }
                        safe_action = safety_filter.validate(proposed_action, state)
                        safety_fallback = safe_action.get("action_id") == -1

                        ts = int(state.get("timestamp", 0))
                        logger.info("Tick=%s severity=%.4f", ts, severity)

                        is_alert = severity >= ANOMALY_SEVERITY_ALERT_THRESHOLD or safety_fallback
                        if is_alert:
                            explanation = (
                                "frequency_unsafe" if safety_fallback else "anomaly_detected"
                            )
                            event_logger.log(
                                {
                                    "timestamp": ts,
                                    "severity": severity,
                                    "action_id": safe_action.get("action_id"),
                                    "target_bus": safe_action.get("target_bus"),
                                    "load_reduction_percent": safe_action.get(
                                        "load_reduction_percent"
                                    ),
                                    "explanation": explanation,
                                }
                            )

                        producer_ref = _get_producer()
                        if producer_ref is not None:
                            out = {
                                "timestamp": ts,
                                "severity_score": severity,
                                "safety_action": safe_action,
                            }
                            try:
                                producer_ref.send(ANOMALY_DETECTION_TOPIC, out)
                                if is_alert:
                                    producer_ref.send(GRID_STATE_ALERTS_TOPIC, out)
                            except kafka_errors.KafkaError as exc:
                                logger.error("Failed to produce output message: %s", exc)

        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
            break
        except kafka_errors.KafkaError as exc:
            logger.warning("Kafka error (%s). Reconnecting in %.1fs...", exc, backoff_s)
            try:
                time.sleep(backoff_s)
            except KeyboardInterrupt:
                logger.info("Shutting down consumer...")
                break
            backoff_s = min(backoff_s * 2, kafka_cfg.reconnect_backoff_max_s)
        except Exception as exc:
            logger.exception("Unexpected error (%s). Reconnecting in %.1fs...", exc, backoff_s)
            try:
                time.sleep(backoff_s)
            except KeyboardInterrupt:
                logger.info("Shutting down consumer...")
                break
            backoff_s = min(backoff_s * 2, kafka_cfg.reconnect_backoff_max_s)
        finally:
            try:
                if consumer is not None:
                    consumer.close()
            except Exception:
                pass

    try:
        producer_ref = producer
        if producer_ref is not None:
            producer_ref.flush(timeout=5)
            producer_ref.close()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Clean exit for interactive runs.
        pass