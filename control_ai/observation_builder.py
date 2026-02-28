"""
Shared observation builder for PPO training and live inference.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

N_BUSES = 39
OBSERVATION_DIM = (N_BUSES * 2) + 1


def build_observation_from_state(state_dict: Dict[str, Any]) -> np.ndarray:
    """
    Build observation vector: 39 voltages + 39 loads + 1 frequency.

    Args:
        state_dict: Grid state payload matching shared message contract.

    Returns:
        np.ndarray: Float32 vector of shape (79,).

    Raises:
        ValueError: If required fields are missing or dimensions are invalid.
    """
    if "voltages" not in state_dict:
        raise ValueError("Missing 'voltages' in state payload")
    if "loads" not in state_dict:
        raise ValueError("Missing 'loads' in state payload")
    if "frequency" not in state_dict:
        raise ValueError("Missing 'frequency' in state payload")

    voltages = np.asarray(state_dict["voltages"], dtype=np.float32)
    loads = np.asarray(state_dict["loads"], dtype=np.float32)
    frequency = np.asarray([state_dict["frequency"]], dtype=np.float32)

    if voltages.shape[0] != N_BUSES:
        raise ValueError(f"Expected {N_BUSES} voltages, got {voltages.shape[0]}")
    if loads.shape[0] != N_BUSES:
        raise ValueError(f"Expected {N_BUSES} loads, got {loads.shape[0]}")

    observation = np.concatenate([voltages, loads, frequency]).astype(np.float32)
    if observation.shape != (OBSERVATION_DIM,):
        raise ValueError(
            f"Unexpected observation shape {observation.shape}, expected ({OBSERVATION_DIM},)"
        )

    return observation
