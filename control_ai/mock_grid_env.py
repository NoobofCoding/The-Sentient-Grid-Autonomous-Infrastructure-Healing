import numpy as np
import random


class GridEnvironment:
    def __init__(self):
        self.num_buses = 39
        self.base_voltage = 1.0
        self.voltages = None
        self.loads = None

    def reset(self):
        """
        Initialize stable grid state.
        """
        self.voltages = np.ones(self.num_buses) * self.base_voltage
        self.loads = np.random.uniform(0.8, 1.2, self.num_buses)

        # Randomly inject fault at one bus
        fault_bus = random.randint(0, self.num_buses - 1)
        self.voltages[fault_bus] = np.random.uniform(0.82, 0.90)

        severity = self._compute_severity()

        return self._build_state(severity)

    def step(self, action_dict):
        """
        Apply control action and simulate voltage response.
        """

        # Apply load reduction effect
        if action_dict["target_bus"] is not None:
            bus = action_dict["target_bus"]

            reduction = action_dict["load_reduction_percent"]

            # Reduce load
            self.loads[bus] *= (1 - reduction)

            # Voltage recovery effect
            self.voltages[bus] += reduction * 0.5

        # Natural voltage drift toward 1.0
        self.voltages += (1.0 - self.voltages) * 0.1

        # Clamp voltages
        self.voltages = np.clip(self.voltages, 0.75, 1.10)

        severity = self._compute_severity()

        return self._build_state(severity)

    def _compute_severity(self):
        """
        Severity = average deviation from 1.0
        """
        deviation = np.mean(np.abs(self.voltages - 1.0))
        return float(np.clip(deviation * 5, 0, 1))

    def _build_state(self, severity):
        return {
            "voltages": self.voltages.tolist(),
            "loads": self.loads.tolist(),
            "severity_score": severity
        }