"""
GridEnvironment for IEEE-39 Bus Digital Twin power grid simulation.

Provides realistic voltage and frequency dynamics, load variations, and
seamless fault injection. Supports deterministic simulation through seed control.
"""

import logging
import random
from typing import Optional, Dict, Any

from .config import (
    N_BUSES,
    N_GENERATORS,
    N_LINES,
    NOMINAL_VOLTAGE,
    NOMINAL_FREQUENCY,
    BASE_LOAD_MW,
    BASE_GENERATION_MW,
    MAX_LOAD_VARIATION_PERCENT,
    VOLTAGE_PROPORTIONAL_DROP,
    VOLTAGE_RANDOM_NOISE,
    FREQUENCY_LOAD_SENSITIVITY,
    FREQUENCY_DAMPING,
    FREQUENCY_RANDOM_NOISE,
    AVERAGE_LINE_FLOW_MULTIPLIER,
    LINE_FLOW_RANDOM_VARIATION,
    MAX_VOLTAGE_ANGLE_DEGREES,
)

# new imports for topology/power flow
from .grid_topology import GridTopology
from .power_flow import PowerFlowCalculator
from .state_builder import GridState
from .fault_injection import FaultInjector

logger = logging.getLogger(__name__)


class GridEnvironment:
    def __init__(
        self,
        auto_fault: bool = False,
        fault_interval: int = 20,
        random_seed: Optional[int] = None,
    ):
        self.timestamp: int = 0
        self.base_load = [BASE_LOAD_MW for _ in range(N_BUSES)]
        self.base_generation = [BASE_GENERATION_MW for _ in range(N_GENERATORS)]

        self.auto_fault = auto_fault
        self.fault_interval = fault_interval
        self.fault_injector = FaultInjector()

        # Frequency state for smooth damping
        self._frequency_state = NOMINAL_FREQUENCY
        self._load_state = sum(self.base_load)

        # topology and power flow helpers (new modular architecture)
        self.topology = GridTopology.default()
        self.powerflow = PowerFlowCalculator()

        # Deterministic simulation support: use independent RNG instance
        self._rng = random.Random(random_seed)
        # Also seed global random to keep modules that use the global RNG deterministic
        if random_seed is not None:
            random.seed(random_seed)
            logger.info(f"GridEnvironment initialized with random seed: {random_seed}")
        else:
            logger.info("GridEnvironment initialized with non-deterministic seed")

    def set_seed(self, seed: int) -> None:
        # Seed both the internal RNG and the global RNG to ensure deterministic
        # behavior across modules that use either `random.Random` instances or
        # the module-level `random` functions (e.g., FaultInjector).
        self._rng.seed(seed)
        random.seed(seed)
        logger.info(f"Random seed set to {seed}")

    def _simulate_loads(self) -> list:
        loads = []
        for base in self.base_load:
            variation = base * MAX_LOAD_VARIATION_PERCENT
            load = base + self._rng.uniform(-variation, variation)
            loads.append(max(0.0, load))  # Prevent negative loads

        return loads

    def _simulate_voltages(self, loads: list) -> list:
        voltages = []
        for load in loads:
            # Proportional voltage drop with load
            drop = load * VOLTAGE_PROPORTIONAL_DROP

            # Nominally 1.0 - drop, plus random noise
            voltage = (
                NOMINAL_VOLTAGE
                - drop
                + self._rng.uniform(-VOLTAGE_RANDOM_NOISE, VOLTAGE_RANDOM_NOISE)
            )

            # Clamp to reasonable bounds (not enforced as hard constraint)
            voltage = max(0.8, min(1.2, voltage))
            voltages.append(voltage)

        return voltages

    def _simulate_voltage_angles(self) -> list:
        return [
            self._rng.uniform(-MAX_VOLTAGE_ANGLE_DEGREES, MAX_VOLTAGE_ANGLE_DEGREES)
            for _ in range(N_BUSES)
        ]

    def _simulate_line_flows(self, loads: list) -> list:
        total_load = sum(loads)
        avg_flow = total_load * AVERAGE_LINE_FLOW_MULTIPLIER / N_LINES

        flows = [
            avg_flow + self._rng.uniform(-LINE_FLOW_RANDOM_VARIATION, LINE_FLOW_RANDOM_VARIATION)
            for _ in range(N_LINES)
        ]

        return flows

    def _simulate_frequency(self, loads: list) -> float:
        total_load = sum(loads)
        total_generation = sum(self.base_generation)

        # Calculate frequency deviation based on imbalance
        imbalance = total_load - total_generation
        raw_frequency_change = imbalance * FREQUENCY_LOAD_SENSITIVITY

        # Apply damping (exponential smoothing)
        self._frequency_state = (
            NOMINAL_FREQUENCY
            + (self._frequency_state - NOMINAL_FREQUENCY) * (1 - FREQUENCY_DAMPING)
            + raw_frequency_change
            + self._rng.uniform(-FREQUENCY_RANDOM_NOISE, FREQUENCY_RANDOM_NOISE)
        )

        # Clamp to reasonable bounds (not hard constraint)
        self._frequency_state = max(48.0, min(52.0, self._frequency_state))

        return self._frequency_state

    def step(self) -> GridState:
        self.timestamp += 1

        # Simulate electrical quantities
        loads = self._simulate_loads()
        # compute voltages via powerflow for modularity; keep old frequency
        try:
            voltages = self.powerflow.compute_voltages(loads)
        except Exception:
            voltages = self._simulate_voltages(loads)

        # frequency uses original dynamic model (damping + noise)
        frequency = self._simulate_frequency(loads)

        voltage_angles = self._simulate_voltage_angles()
        line_flows = self._simulate_line_flows(loads)

        # Create state object
        state = GridState(
            timestamp=float(self.timestamp),
            voltages=voltages,
            voltage_angles=voltage_angles,
            loads=loads,
            generator_outputs=self.base_generation.copy(),
            line_flows=line_flows,
            frequency=frequency,
        )

        # Apply ongoing fault if active
        state = self.fault_injector.apply_active_fault(state)

        # Trigger automatic fault injection at intervals
        if self.auto_fault and self.timestamp % self.fault_interval == 0:
            fault_types = ["voltage_sag", "frequency", "load_spike"]
            fault_type = fault_types[self._rng.randint(0, len(fault_types) - 1)]

            if fault_type == "voltage_sag":
                state = self.fault_injector.inject_voltage_sag(state)
            elif fault_type == "frequency":
                state = self.fault_injector.inject_frequency_disturbance(state)
            elif fault_type == "load_spike":
                state = self.fault_injector.inject_load_spike(state)

            logger.info(f"Auto-triggered fault at t={self.timestamp}: {fault_type}")

        return state

    def step_multiple(self, count: int) -> list:
        
        states = []
        for _ in range(count):
            states.append(self.step())

        return states

    def get_status(self) -> Dict[str, Any]:
        
        return {
            "timestamp": self.timestamp,
            "total_load": sum(self.base_load),
            "total_generation": sum(self.base_generation),
            "auto_fault_enabled": self.auto_fault,
            "fault_interval": self.fault_interval,
            "fault_status": self.fault_injector.get_fault_status(),
        }

    # --- topology helpers --------------------------------------------------
    def get_bus_info(self, bus_id: int):
        
        return self.topology.get_bus_info(bus_id)

    def get_generator_info(self, gen_id: int):
        
        return self.topology.get_generator_info(gen_id)

    def get_load_info(self, load_id: int):
        
        return self.topology.get_load_info(load_id)

    def reset(self, random_seed: Optional[int] = None) -> None:
        
        self.timestamp = 0
        self._frequency_state = NOMINAL_FREQUENCY
        self._load_state = sum(self.base_load)
        self.fault_injector.reset()

        if random_seed is not None:
            # reseed internal RNG
            self._rng.seed(random_seed)
        logger.info("GridEnvironment reset to initial state")