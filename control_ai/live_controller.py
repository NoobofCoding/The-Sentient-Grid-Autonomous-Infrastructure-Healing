"""
Live Control AI entrypoint.

Consumes GridState messages from Kafka, validates against shared JSON schema,
runs deterministic PPO inference, and publishes control actions.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

from jsonschema import ValidationError, validate
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from control_ai.policy_inference import ModelLoadError, PolicyInference
from control_ai.observation_builder import build_observation_from_state
from control_ai.reward_engine import calculate_reward
from intelligence.anomaly_detection.detector_service import AnomalyDetectionService
from intelligence.logging.event_logger import EventLogger
from intelligence.safety.safety_filter import SafetyFilter
from intelligence.safety.stability_checker import is_frequency_safe
from shared.action_contracts import action_from_id, validate_action_payload
from shared.constants import CONTRACT_VERSION, KAFKA_BOOTSTRAP_SERVERS
from shared.message_contracts import (
    build_pillar4_payload,
    infer_disturbance_type,
    validate_pillar4_payload,
)
from shared.topic_names import (
    ANALYTICS_TOPIC,
    ANOMALY_DETECTION_TOPIC,
    GRID_ACTION_TOPIC,
    GRID_STATE_TOPIC,
)


LOGGER = logging.getLogger("control_ai.live_controller")
SCHEMA_PATH = PROJECT_ROOT / "shared" / "message_schema.json"
CONSUMER_GROUP_ID = "control_ai_group"
RETRY_DELAY_SECONDS = 5


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_grid_state_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        GRID_STATE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=CONSUMER_GROUP_ID,
        consumer_timeout_ms=1000,
        request_timeout_ms=30000,
        session_timeout_ms=10000,
    )


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        retries=3,
        request_timeout_ms=30000,
        acks="all",
    )


def run() -> None:
    configure_logging()
    LOGGER.info("Control AI live controller starting")
    LOGGER.info("Contract version: %s", CONTRACT_VERSION)
    LOGGER.info("Subscribing to topic: %s", GRID_STATE_TOPIC)
    LOGGER.info("Publishing actions to topic: %s", GRID_ACTION_TOPIC)
    LOGGER.info("Kafka bootstrap servers: %s", KAFKA_BOOTSTRAP_SERVERS)

    try:
        schema = load_grid_state_schema()
    except Exception as exc:
        LOGGER.error("Failed to load schema at %s: %s", SCHEMA_PATH, exc)
        raise SystemExit(1) from exc

    try:
        inference_engine = PolicyInference()
        inference_engine.load_model()
        LOGGER.info("PPO model loaded successfully")
    except ModelLoadError as exc:
        LOGGER.error("Model initialization failed: %s", exc)
        raise SystemExit(1) from exc

    consumer = None
    producer = None
    detector = None
    safety_filter = SafetyFilter()
    compliance_logger = EventLogger()
    prev_enriched_state = None

    try:
        while True:
            try:
                consumer = create_consumer()
                producer = create_producer()
                LOGGER.info("Kafka consumer/producer connected")

                while True:
                    batches = consumer.poll(timeout_ms=1000)
                    if not batches:
                        continue

                    for records in batches.values():
                        for message in records:
                            state_dict = message.value

                            try:
                                validate(instance=state_dict, schema=schema)
                            except ValidationError as exc:
                                LOGGER.warning("Validation failure. Skipping message: %s", exc.message)
                                continue

                            timestamp = state_dict.get("timestamp")
                            LOGGER.info("State received | timestamp=%s", timestamp)

                            if detector is None:
                                feature_count = len(state_dict["voltages"]) + len(state_dict["loads"]) + 1
                                detector = AnomalyDetectionService(input_dim=feature_count)
                                LOGGER.info("Anomaly detector initialized | input_dim=%s", feature_count)

                            try:
                                anomaly_result = detector.process(state_dict)
                                severity_score = float(anomaly_result["severity_score"])
                            except Exception as exc:
                                LOGGER.error(
                                    "Anomaly detection failed | timestamp=%s | error=%s",
                                    timestamp,
                                    exc,
                                )
                                continue

                            enriched_state = dict(state_dict)
                            enriched_state["severity_score"] = severity_score

                            try:
                                observation = build_observation_from_state(state_dict)
                            except Exception as exc:
                                LOGGER.error(
                                    "Observation build failed | timestamp=%s | error=%s",
                                    timestamp,
                                    exc,
                                )
                                continue

                            expected_shape = inference_engine.expected_observation_shape()

                            if observation.shape != expected_shape:
                                LOGGER.error(
                                    "Observation shape mismatch | timestamp=%s | observed=%s | expected=%s",
                                    timestamp,
                                    observation.shape,
                                    expected_shape,
                                )
                                continue

                            try:
                                start = time.perf_counter()
                                action_dict = inference_engine.infer_action(
                                    state_dict,
                                    observation=observation,
                                )
                                latency_ms = (time.perf_counter() - start) * 1000.0
                            except AssertionError as exc:
                                LOGGER.error(
                                    "Model shape assertion failed | timestamp=%s | observed=%s | expected=%s | error=%s",
                                    timestamp,
                                    observation.shape,
                                    expected_shape,
                                    exc,
                                )
                                continue
                            except Exception as exc:
                                LOGGER.exception(
                                    "Model inference failed | timestamp=%s | observed=%s | expected=%s | error=%s",
                                    timestamp,
                                    observation.shape,
                                    expected_shape,
                                    exc,
                                )
                                continue

                            proposed_action = dict(action_dict)
                            try:
                                safe_action = safety_filter.validate(dict(proposed_action), state_dict)
                            except Exception as exc:
                                LOGGER.error(
                                    "Safety filter failed | timestamp=%s | action=%s | error=%s",
                                    timestamp,
                                    proposed_action,
                                    exc,
                                )
                                continue

                            safety_override_flag = safe_action != proposed_action

                            if safe_action.get("action_id") == -1:
                                fallback = action_from_id(0)
                                fallback["model_version"] = CONTRACT_VERSION
                                safe_action = fallback
                                safety_override_flag = True

                            try:
                                validate_action_payload(safe_action)
                            except Exception as exc:
                                LOGGER.error(
                                    "Action contract validation failed | timestamp=%s | action=%s | error=%s",
                                    timestamp,
                                    safe_action,
                                    exc,
                                )
                                continue

                            disturbance_type = infer_disturbance_type(state_dict, severity_score)

                            frequency = float(state_dict["frequency"])
                            stable_frequency = is_frequency_safe(frequency)
                            stability_status = "stable" if stable_frequency and severity_score < 0.7 else "unstable"

                            if prev_enriched_state is None:
                                reward = 0.0
                            else:
                                reward = calculate_reward(prev_enriched_state, enriched_state, safe_action)

                            anomaly_to_rl = {
                                "voltages": state_dict["voltages"],
                                "loads": state_dict["loads"],
                                "severity_score": severity_score,
                            }

                            analytics_payload = build_pillar4_payload(
                                timestamp=timestamp,
                                bus_voltages=state_dict["voltages"],
                                load_levels=state_dict["loads"],
                                disturbance_type=disturbance_type,
                                rl_action=safe_action,
                                safety_override_flag=safety_override_flag,
                                reward=reward,
                                stability_status=stability_status,
                            )

                            try:
                                validate_pillar4_payload(analytics_payload)
                            except Exception as exc:
                                LOGGER.error(
                                    "Pillar 4 payload validation failed | timestamp=%s | error=%s",
                                    timestamp,
                                    exc,
                                )
                                continue

                            try:
                                compliance_logger.log(
                                    {
                                        "timestamp": int(timestamp) if timestamp is not None else 0,
                                        "severity": severity_score,
                                        "action_id": safe_action["action_id"],
                                        "target_bus": safe_action["target_bus"],
                                        "load_reduction_percent": safe_action["load_reduction_percent"],
                                        "explanation": (
                                            f"disturbance={disturbance_type};"
                                            f"override={safety_override_flag};"
                                            f"stability={stability_status}"
                                        ),
                                    }
                                )
                            except Exception as exc:
                                LOGGER.error(
                                    "Compliance log failed | timestamp=%s | error=%s",
                                    timestamp,
                                    exc,
                                )

                            action_json = json.dumps(safe_action)
                            analytics_json = json.dumps(analytics_payload)
                            anomaly_json = json.dumps(anomaly_to_rl)

                            LOGGER.info(
                                "Action decided | timestamp=%s | action=%s | latency=%.2fms | target_bus=%s | load_reduction=%.3f",
                                timestamp,
                                safe_action["action_id"],
                                latency_ms,
                                safe_action["target_bus"],
                                safe_action["load_reduction_percent"],
                            )
                            LOGGER.info(
                                "Pillar3 decision | timestamp=%s | severity=%.4f | disturbance=%s | override=%s | stability=%s",
                                timestamp,
                                severity_score,
                                disturbance_type,
                                safety_override_flag,
                                stability_status,
                            )

                            future = producer.send(GRID_ACTION_TOPIC, action_json.encode("utf-8"))
                            future.get(timeout=10)
                            producer.send(ANOMALY_DETECTION_TOPIC, anomaly_json.encode("utf-8"))
                            producer.send(ANALYTICS_TOPIC, analytics_json.encode("utf-8"))

                            prev_enriched_state = enriched_state

            except KeyboardInterrupt:
                LOGGER.info("KeyboardInterrupt received. Initiating clean shutdown")
                break
            except NoBrokersAvailable as exc:
                LOGGER.error("Kafka broker unavailable: %s. Retrying in %ss", exc, RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)
            except KafkaError as exc:
                LOGGER.error("Kafka connection error: %s. Retrying in %ss", exc, RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)
            except Exception as exc:
                LOGGER.error("Unexpected runtime error: %s. Retrying in %ss", exc, RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)
            finally:
                if consumer is not None:
                    try:
                        consumer.close()
                    except Exception:
                        pass
                    consumer = None

                if producer is not None:
                    try:
                        producer.flush(timeout=10)
                        producer.close()
                    except Exception:
                        pass
                    producer = None

    finally:
        LOGGER.info("Control AI live controller stopped")


if __name__ == "__main__":
    run()