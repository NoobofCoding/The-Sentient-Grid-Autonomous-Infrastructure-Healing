"""
Fault injection module for IEEE-39 Bus Digital Twin.

Supports multiple fault types including voltage sag, frequency disturbance,
and load spike faults. Faults automatically recover after a configurable duration.
"""

import copy
import logging
import random
from typing import Optional, Tuple, Dict, Any
from enum import Enum

from .config import (
    FAULT_VOLTAGE_DROP,
    FAULT_FREQUENCY_DEVIATION,
    FAULT_LOAD_SPIKE_PERCENT,
    FAULT_DURATION_STEPS,
    FAULT_RECOVERY_STEPS,
    N_BUSES,
    N_GENERATORS,
)
from .state_builder import GridState

logger = logging.getLogger(__name__)


class FaultType(Enum):
    """Enumeration of supported fault types."""
    VOLTAGE_SAG = "voltage_sag"
    FREQUENCY_DISTURBANCE = "frequency_disturbance"
    LOAD_SPIKE = "load_spike"


class FaultInjector:
    """
    Manages fault injection and recovery for the power grid digital twin.

    Supports multiple fault types with automatic tracking and recovery.
    Faults are applied over a specified duration, after which the system
    gradually recovers to normal operation.

    Attributes:
        active_fault: Tuple of (FaultType, bus_or_generator_index) for current fault.
        remaining_steps: Steps until current fault recovers.
        fault_history: List of all injected faults with timestamps.
    """

    def __init__(self):
        """Initialize the fault injector with no active faults."""
        self.active_fault: Optional[Tuple[FaultType, int]] = None
        self.remaining_steps: int = 0
        self.recovery_progress: float = 0.0  # 0.0 to 1.0
        self.fault_history: list = []
        logger.info("FaultInjector initialized")

    def inject_voltage_sag(
        self,
        state: GridState,
        bus_index: Optional[int] = None,
        magnitude: Optional[float] = None,
    ) -> GridState:
        """
        Inject a voltage sag fault on a specified or random bus.

        A voltage sag reduces voltage at a bus by a specified amount.
        This fault persists for FAULT_DURATION_STEPS and then recovers.

        Args:
            state (GridState): Current grid state.
            bus_index (Optional[int]): Bus to fault. If None, randomly selected.
            magnitude (Optional[float]): Voltage drop magnitude (0-1 p.u.).
                                       If None, uses FAULT_VOLTAGE_DROP.

        Returns:
            GridState: Grid state with voltage sag applied.

        Raises:
            IndexError: If bus_index is out of range.
        """
        new_state = copy.deepcopy(state)

        if bus_index is None:
            bus_index = random.randint(0, N_BUSES - 1)

        if bus_index < 0 or bus_index >= N_BUSES:
            raise IndexError(f"Bus index {bus_index} out of range [0, {N_BUSES-1}]")

        if magnitude is None:
            magnitude = FAULT_VOLTAGE_DROP

        original_voltage = new_state.voltages[bus_index]
        new_state.voltages[bus_index] *= (1 - magnitude)

        self.active_fault = (FaultType.VOLTAGE_SAG, bus_index)
        self.remaining_steps = FAULT_DURATION_STEPS
        self.recovery_progress = 0.0
        new_state.is_faulted = True
        new_state.fault_info = {
            "type": FaultType.VOLTAGE_SAG.value,
            "bus": bus_index,
            "original_voltage": original_voltage,
            "faulted_voltage": new_state.voltages[bus_index],
            "magnitude": magnitude,
            "duration_steps": FAULT_DURATION_STEPS,
        }

        logger.warning(
            f"Voltage sag fault injected on bus {bus_index}: "
            f"{original_voltage:.3f}p.u. → {new_state.voltages[bus_index]:.3f}p.u."
        )

        self.fault_history.append(
            {
                "type": "voltage_sag",
                "bus": bus_index,
                "timestamp": state.timestamp,
            }
        )

        return new_state

    def inject_frequency_disturbance(
        self,
        state: GridState,
        deviation: Optional[float] = None,
    ) -> GridState:
        """
        Inject a frequency disturbance fault affecting the entire system.

        Frequency disturbance simulates sudden changes in system balance
        (e.g., generator loss or large load disconnect). The disturbance
        persists for FAULT_DURATION_STEPS.

        Args:
            state (GridState): Current grid state.
            deviation (Optional[float]): Frequency deviation in Hz.
                                       If None, uses ±FAULT_FREQUENCY_DEVIATION.

        Returns:
            GridState: Grid state with frequency disturbance applied.
        """
        new_state = copy.deepcopy(state)

        if deviation is None:
            # Randomly choose positive or negative deviation
            sign = random.choice([-1, 1])
            deviation = sign * FAULT_FREQUENCY_DEVIATION

        original_frequency = new_state.frequency
        new_state.frequency += deviation

        self.active_fault = (FaultType.FREQUENCY_DISTURBANCE, 0)
        self.remaining_steps = FAULT_DURATION_STEPS
        self.recovery_progress = 0.0
        new_state.is_faulted = True
        new_state.fault_info = {
            "type": FaultType.FREQUENCY_DISTURBANCE.value,
            "original_frequency": original_frequency,
            "faulted_frequency": new_state.frequency,
            "deviation": deviation,
            "duration_steps": FAULT_DURATION_STEPS,
        }

        logger.warning(
            f"Frequency disturbance injected: "
            f"{original_frequency:.2f}Hz → {new_state.frequency:.2f}Hz ({deviation:+.2f}Hz)"
        )

        self.fault_history.append(
            {
                "type": "frequency_disturbance",
                "deviation": deviation,
                "timestamp": state.timestamp,
            }
        )

        return new_state

    def inject_load_spike(
        self,
        state: GridState,
        bus_index: Optional[int] = None,
        spike_percent: Optional[float] = None,
    ) -> GridState:
        """
        Inject a load spike fault on a specified or random bus.

        Load spike simulates sudden increase in consumption at a bus
        (e.g., industrial equipment startup).

        Args:
            state (GridState): Current grid state.
            bus_index (Optional[int]): Bus to fault. If None, randomly selected.
            spike_percent (Optional[float]): Load increase as fraction (0-1).
                                           If None, uses FAULT_LOAD_SPIKE_PERCENT.

        Returns:
            GridState: Grid state with load spike applied.

        Raises:
            IndexError: If bus_index is out of range.
        """
        new_state = copy.deepcopy(state)

        if bus_index is None:
            bus_index = random.randint(0, N_BUSES - 1)

        if bus_index < 0 or bus_index >= N_BUSES:
            raise IndexError(f"Bus index {bus_index} out of range [0, {N_BUSES-1}]")

        if spike_percent is None:
            spike_percent = FAULT_LOAD_SPIKE_PERCENT

        original_load = new_state.loads[bus_index]
        new_state.loads[bus_index] *= (1 + spike_percent)

        self.active_fault = (FaultType.LOAD_SPIKE, bus_index)
        self.remaining_steps = FAULT_DURATION_STEPS
        self.recovery_progress = 0.0
        new_state.is_faulted = True
        new_state.fault_info = {
            "type": FaultType.LOAD_SPIKE.value,
            "bus": bus_index,
            "original_load": original_load,
            "spiked_load": new_state.loads[bus_index],
            "spike_percent": spike_percent,
            "duration_steps": FAULT_DURATION_STEPS,
        }

        logger.warning(
            f"Load spike fault injected on bus {bus_index}: "
            f"{original_load:.1f}MW → {new_state.loads[bus_index]:.1f}MW ({spike_percent*100:.1f}%)"
        )

        self.fault_history.append(
            {
                "type": "load_spike",
                "bus": bus_index,
                "timestamp": state.timestamp,
            }
        )

        return new_state

    def apply_active_fault(self, state: GridState) -> GridState:
        """
        Apply active fault and manage recovery for one simulation step.

        If a fault is active, it continues to affect the grid while
        transitioning toward recovery. Faults must be explicitly injected
        again if they should persist beyond FAULT_DURATION_STEPS.

        Args:
            state (GridState): Current grid state before fault application.

        Returns:
            GridState: Modified state with fault applied or recovered.
        """
        # If no active fault or fault already expired, return state unchanged
        if not self.active_fault or self.remaining_steps <= 0:
            if self.active_fault and self.remaining_steps <= 0:
                # clear fault metadata
                logger.info(f"Fault recovery complete for {self.active_fault}")
                self.active_fault = None
                self.recovery_progress = 0.0
                new_state = copy.deepcopy(state)
                new_state.is_faulted = False
                new_state.fault_info = None
                return new_state
            return state

        fault_type, index = self.active_fault

        # Apply effect without re-injecting (magnitude already applied earlier)
        new_state = copy.deepcopy(state)
        if fault_type == FaultType.VOLTAGE_SAG:
            # voltage already sagged during injection; keep state as-is
            pass
        elif fault_type == FaultType.FREQUENCY_DISTURBANCE:
            pass
        elif fault_type == FaultType.LOAD_SPIKE:
            pass
        else:
            logger.error(f"Unknown fault type: {fault_type}")

        # decrement remaining steps and update progress
        self.remaining_steps -= 1
        if self.remaining_steps <= 0:
            self.recovery_progress = 1.0
            logger.info(
                f"Fault {fault_type.value} at index {index} entering recovery phase"
            )
        else:
            self.recovery_progress = max(
                0.0, 1.0 - (self.remaining_steps / FAULT_DURATION_STEPS)
            )

        return new_state

    def get_fault_status(self) -> Dict[str, Any]:
        """
        Get current status of fault injection system.

        Returns:
            Dict[str, Any]: Dictionary with fault status information.
        """
        return {
            "has_active_fault": self.active_fault is not None,
            "fault_type": self.active_fault[0].value if self.active_fault else None,
            "index": self.active_fault[1] if self.active_fault else None,
            "remaining_steps": self.remaining_steps,
            "recovery_progress": self.recovery_progress,
            "total_faults_injected": len(self.fault_history),
        }

    def reset(self) -> None:
        """Reset fault injector to initial state."""
        self.active_fault = None
        self.remaining_steps = 0
        self.recovery_progress = 0.0
        self.fault_history.clear()
        logger.info("FaultInjector reset to initial state")
        # nothing to return

    def clear_fault(self):
        self.active_fault = None
        self.remaining_steps = 0