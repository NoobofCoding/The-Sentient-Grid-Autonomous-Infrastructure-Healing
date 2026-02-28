"""Prototype policy inference with optional PPO and lightweight fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np

from control_ai.observation_builder import build_observation_from_state
from shared.action_contracts import action_from_id
from shared.constants import CONTRACT_VERSION


MODEL_PATH = Path(__file__).resolve().parent / "models" / "sentient_grid_ppo.zip"


class ModelLoadError(RuntimeError):
    """Raised when PPO model cannot be loaded for inference."""


class PolicyInference:
    """Inference wrapper: uses PPO if available, otherwise heuristic policy."""

    def __init__(self, model_path: Path = MODEL_PATH, model_version: str = CONTRACT_VERSION):
        self.model_path = Path(model_path)
        self.model_version = model_version
        self._model: Any | None = None

    def load_model(self) -> None:
        """Attempt PPO load; gracefully fall back to heuristic mode."""
        if not self.model_path.exists():
            self._model = None
            return

        try:
            from stable_baselines3 import PPO
            self._model = PPO.load(str(self.model_path))
        except Exception:
            self._model = None

    def expected_observation_shape(self) -> tuple[int, ...]:
        if self._model is None:
            return (79,)
        return tuple(self._model.observation_space.shape)

    def infer_action(
        self,
        state_dict: Dict[str, Any],
        observation: np.ndarray | None = None,
    ) -> Dict[str, Any]:
        """
        Run deterministic policy inference and return action contract payload.
        """
        if self._model is None and observation is None:
            self.load_model()

        state_vector = observation if observation is not None else build_observation_from_state(state_dict)
        expected_shape = self.expected_observation_shape()
        assert state_vector.shape == expected_shape, (
            f"Unexpected observation shape {state_vector.shape} for Box environment, "
            f"expected {expected_shape}"
        )

        action_id = 0
        if self._model is None:
            action_id = self._rule_action(state_dict)
        else:
            model_action, _ = self._model.predict(state_vector, deterministic=True)
            action_id = int(model_action)
            rule_action = self._rule_action(state_dict)
            if rule_action != 0:
                action_id = rule_action

        action_payload = action_from_id(int(action_id))
        action_payload["model_version"] = self.model_version
        return action_payload

    def _rule_action(self, state_dict: Dict[str, Any]) -> int:
        """Prototype disturbance override for obvious voltage/frequency events."""
        severity = float(state_dict.get("severity_score", 0.0))
        frequency = float(state_dict.get("frequency", 50.0))
        voltages = np.asarray(state_dict.get("voltages", []), dtype=np.float32)

        voltage_sag = float(voltages.min()) < 0.95 if voltages.size else False
        voltage_spike = float(voltages.max()) > 1.05 if voltages.size else False
        frequency_disturbance = frequency < 49.7 or frequency > 50.3

        if severity >= 0.80 or frequency < 49.5 or frequency > 50.5:
            return 2
        if voltage_sag or voltage_spike or frequency_disturbance or severity >= 0.45:
            return 1
        if severity >= 0.30:
            return 3
        return 0


def get_action(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Backwards-compatible helper used by existing tests/scripts."""
    engine = PolicyInference()
    return engine.infer_action(state_dict)