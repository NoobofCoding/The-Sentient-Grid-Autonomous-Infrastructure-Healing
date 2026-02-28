from __future__ import annotations

from typing import Any, Dict

import numpy as np


class AnomalyDetectionService:
    def __init__(self, input_dim: int):
        self.input_dim = int(input_dim)

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        voltages = np.asarray(message.get("voltages", []), dtype=np.float32)
        loads = np.asarray(message.get("loads", []), dtype=np.float32)
        frequency = float(message.get("frequency", 50.0))

        if voltages.size == 0 or loads.size == 0:
            return {
                "voltages": message.get("voltages", []),
                "loads": message.get("loads", []),
                "severity_score": 0.0,
            }

        voltage_dev = float(np.mean(np.abs(voltages - 1.0)))
        load_spread = float(np.std(loads) / (np.mean(loads) + 1e-6))
        freq_dev = abs(frequency - 50.0)

        severity = min(1.0, (voltage_dev * 4.0) + (freq_dev * 0.8) + (load_spread * 1.2))

        return {
            "voltages": message["voltages"],
            "loads": message["loads"],
            "severity_score": float(severity),
        }