"""Prototype autonomous orchestrator (no Docker/Kafka required).

Pipeline:
Pillar 1 (Digital Twin) -> Pillar 3 (Anomaly Detection) ->
Pillar 2 (Policy Inference) -> Safety Filter -> Pillar 4 (Analytics/Logging) ->
Dashboard bridge (/current_state)
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from control_ai.observation_builder import build_observation_from_state
from control_ai.policy_inference import PolicyInference
from control_ai.reward_engine import calculate_reward
from infrastructure.digital_twin.grid_env import GridEnvironment
from intelligence.anomaly_detection.detector_service import AnomalyDetectionService
from intelligence.logging.event_logger import EventLogger
from intelligence.safety.safety_filter import SafetyFilter
from intelligence.safety.stability_checker import is_frequency_safe
from interface.api.bridge import DashboardStateStore, create_bridge_server
from Visual.explainability.explainer import generate_explanation
from Visual.explainability.summary_builder import build_summary
from shared.action_contracts import action_from_id
from shared.message_contracts import build_pillar4_payload, infer_disturbance_type

LOGGER = logging.getLogger("main_autonomous_system")


@dataclass
class QueuedState:
    state: Dict[str, Any]


class AutonomousSystem:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.state_queue: Queue[QueuedState] = Queue(maxsize=128)
        self.dashboard_state = DashboardStateStore()

        self.environment = GridEnvironment(auto_fault=True, fault_interval=40)
        self.detector = AnomalyDetectionService(input_dim=79)
        self.policy = PolicyInference()
        self.safety_filter = SafetyFilter()

        self.prev_state: Dict[str, Any] | None = None
        self.bridge_server = None
        self.last_tick_time = 0.0
        self.last_explanation: str = "Analyzing grid behavior..."

    def setup(self) -> None:
        self._configure_logging()
        self.policy.load_model()
        self._start_dashboard_bridge()
        LOGGER.info("Autonomous prototype started (local in-process mode)")

    def _configure_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

    def _start_dashboard_bridge(self) -> None:
        self.bridge_server = create_bridge_server("0.0.0.0", 8088, self.dashboard_state)
        thread = threading.Thread(target=self.bridge_server.serve_forever, daemon=True, name="dashboard-bridge")
        thread.start()
        LOGGER.info("Dashboard bridge listening at http://127.0.0.1:8088/current_state")

    def run(self) -> None:
        producer_thread = threading.Thread(target=self._produce_states, daemon=True, name="state-producer")
        processor_thread = threading.Thread(target=self._process_states, daemon=True, name="state-processor")

        producer_thread.start()
        processor_thread.start()

        try:
            while not self.stop_event.is_set():
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.stop_event.set()
        finally:
            self.shutdown()

    def _produce_states(self) -> None:
        while not self.stop_event.is_set():
            try:
                state_obj = self.environment.step()
                state = state_obj.to_dict()
                self.state_queue.put(QueuedState(state=state), timeout=0.2)
                time.sleep(0.2)
            except Exception as exc:
                LOGGER.error("State production failed: %s", exc)
                time.sleep(0.2)

    def _process_states(self) -> None:
        event_logger = EventLogger()

        while not self.stop_event.is_set():
            try:
                queued = self.state_queue.get(timeout=0.5)
            except Empty:
                continue

            start = time.perf_counter()
            state = queued.state

            anomaly = self.detector.process(state)
            severity_score = float(anomaly.get("severity_score", 0.0))
            anomaly_detected = severity_score >= 0.5

            state_with_severity = dict(state)
            state_with_severity["severity_score"] = severity_score

            observation = build_observation_from_state(state)
            proposed_action = self.policy.infer_action(state_with_severity, observation=observation)
            safe_action = self.safety_filter.validate(dict(proposed_action), state)
            safe_action["model_version"] = proposed_action.get("model_version", "prototype")

            if safe_action.get("action_id") not in (0, 1, 2, 3):
                safe_action = action_from_id(0)
                safe_action["model_version"] = "prototype"

            if self.prev_state is None:
                reward = 0.0
            else:
                reward = calculate_reward(self.prev_state, state_with_severity, safe_action)

            disturbance_type = infer_disturbance_type(state, severity_score)
            stability_status = "stable" if (is_frequency_safe(float(state["frequency"])) and severity_score < 0.7) else "unstable"

            analytics_payload = build_pillar4_payload(
                timestamp=state["timestamp"],
                bus_voltages=state["voltages"],
                load_levels=state["loads"],
                disturbance_type=disturbance_type,
                rl_action=safe_action,
                safety_override_flag=(safe_action != proposed_action),
                reward=reward,
                stability_status=stability_status,
            )

            should_refresh_explanation = (
                int(state["timestamp"]) % 10 == 0
                or anomaly_detected
                or safe_action.get("action_id", 0) != 0
            )
            if should_refresh_explanation:
                try:
                    summary = build_summary(
                        {
                            "bus_voltages": state["voltages"],
                            "action": safe_action,
                            "reward": reward,
                            "safety_override": (safe_action != proposed_action),
                        }
                    )
                    self.last_explanation = generate_explanation(summary)
                except Exception:
                    pass

            try:
                event_logger.log(
                    {
                        "timestamp": int(state["timestamp"]),
                        "severity": severity_score,
                        "action_id": safe_action["action_id"],
                        "target_bus": safe_action["target_bus"],
                        "load_reduction_percent": safe_action["load_reduction_percent"],
                        "explanation": (
                            f"anomaly={anomaly_detected};"
                            f"disturbance={disturbance_type};"
                            f"stability={stability_status}"
                        ),
                    }
                )
            except Exception:
                pass

            self.dashboard_state.update(
                {
                    "timestamp": state["timestamp"],
                    "voltages": state["voltages"],
                    "loads": state["loads"],
                    "frequency": state["frequency"],
                    "severity_score": severity_score,
                    "anomaly_detected": anomaly_detected,
                    "action": safe_action,
                    "stability_status": analytics_payload["stability_status"],
                    "reward": analytics_payload["reward"],
                    "operator_explanation": self.last_explanation,
                }
            )

            self.prev_state = state_with_severity
            self.last_tick_time = time.time()

            latency_ms = (time.perf_counter() - start) * 1000.0
            LOGGER.info(
                "Tick processed | t=%s | severity=%.3f | action=%s | latency=%.1fms",
                state["timestamp"],
                severity_score,
                safe_action["action_id"],
                latency_ms,
            )

    def shutdown(self) -> None:
        self.stop_event.set()
        if self.bridge_server is not None:
            self.bridge_server.shutdown()
            self.bridge_server.server_close()
        LOGGER.info("Autonomous system stopped")


def main() -> None:
    system = AutonomousSystem()

    def _handle_signal(_signum: int, _frame: Any) -> None:
        system.stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    system.setup()
    system.run()


if __name__ == "__main__":
    main()
