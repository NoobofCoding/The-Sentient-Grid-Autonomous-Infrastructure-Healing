"""
GridState dataclass and builder for IEEE-39 Bus Digital Twin.

This module defines the core data structure for representing power grid state
at any point in time, with comprehensive validation and serialization support.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from .config import (
    N_BUSES,
    N_GENERATORS,
    N_LINES,
    NOMINAL_VOLTAGE,
    NOMINAL_FREQUENCY,
    MIN_VOLTAGE,
    MAX_VOLTAGE,
    MIN_FREQUENCY,
    MAX_FREQUENCY,
    VOLTAGE_TOLERANCE,
    FREQUENCY_TOLERANCE,
)

logger = logging.getLogger(__name__)


@dataclass
class GridState:
    """
    Represents the complete instantaneous state of the IEEE-39 bus power system.

    This dataclass captures all electrical quantities at a specific timestamp,
    enabling analysis, logging, and control decisions. All arrays are validated
    for correctness dimensions.

    Attributes:
        timestamp (float): Simulation time in seconds.
        voltages (List[float]): Bus voltages in p.u. (39 values).
        voltage_angles (List[float]): Bus voltage angles in degrees (39 values).
        loads (List[float]): Bus loads in MW (39 values).
        generator_outputs (List[float]): Generator outputs in MW (10 values).
        line_flows (List[float]): Transmission line power flows in MW (46 values).
        frequency (float): System frequency in Hz.
        is_faulted (bool): Flag indicating if a fault is currently active.
        fault_info (Optional[Dict[str, Any]]): Metadata about active fault.
    """

    timestamp: float
    voltages: List[float]
    voltage_angles: List[float]
    loads: List[float]
    generator_outputs: List[float]
    line_flows: List[float]
    frequency: float
    is_faulted: bool = False
    fault_info: Optional[Dict[str, Any]] = field(default=None)

    def __post_init__(self) -> None:
        """Validate grid state after initialization."""
        self._validate_dimensions()
        self._validate_values()

    def _validate_dimensions(self) -> None:
        """
        Validate that all arrays have correct dimensions.

        Raises:
            ValueError: If any array has incorrect length.
        """
        if len(self.voltages) != N_BUSES:
            raise ValueError(
                f"Voltages must have {N_BUSES} elements, got {len(self.voltages)}"
            )

        if len(self.voltage_angles) != N_BUSES:
            raise ValueError(
                f"Voltage angles must have {N_BUSES} elements, "
                f"got {len(self.voltage_angles)}"
            )

        if len(self.loads) != N_BUSES:
            raise ValueError(
                f"Loads must have {N_BUSES} elements, got {len(self.loads)}"
            )

        if len(self.generator_outputs) != N_GENERATORS:
            raise ValueError(
                f"Generator outputs must have {N_GENERATORS} elements, "
                f"got {len(self.generator_outputs)}"
            )

        if len(self.line_flows) != N_LINES:
            raise ValueError(
                f"Line flows must have {N_LINES} elements, "
                f"got {len(self.line_flows)}"
            )

        logger.debug(
            f"GridState dimensions validated: {N_BUSES} buses, "
            f"{N_GENERATORS} generators, {N_LINES} lines"
        )

    def _validate_values(self) -> None:
        """
        Validate that electrical values are within acceptable ranges.

        Issues warnings for values outside normal operating bounds.
        """
        # Check voltages
        out_of_bounds_voltages = [
            (i, v) for i, v in enumerate(self.voltages)
            if v < MIN_VOLTAGE - VOLTAGE_TOLERANCE or v > MAX_VOLTAGE + VOLTAGE_TOLERANCE
        ]
        if out_of_bounds_voltages:
            logger.warning(
                f"Out-of-bounds voltages at t={self.timestamp}: {out_of_bounds_voltages}"
            )

        # Check frequency
        if (self.frequency < MIN_FREQUENCY - FREQUENCY_TOLERANCE or
                self.frequency > MAX_FREQUENCY + FREQUENCY_TOLERANCE):
            logger.warning(
                f"Out-of-bounds frequency at t={self.timestamp}: {self.frequency} Hz"
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert GridState to a JSON-serializable dictionary.

        Returns:
            Dict[str, Any]: Serialized representation of the grid state.
        """
        return asdict(self)

    def to_compact_dict(self) -> Dict[str, Any]:
        """
        Convert GridState to a compact dictionary for efficient transmission.

        Returns:
            Dict[str, Any]: Compact serialized representation.
        """
        return {
            "t": self.timestamp,
            "v": self.voltages,
            "a": self.voltage_angles,
            "l": self.loads,
            "g": self.generator_outputs,
            "f": self.line_flows,
            "s": self.frequency,
            "faulted": self.is_faulted,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "GridState":
        """
        Construct GridState from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary with GridState fields.

        Returns:
            GridState: Reconstructed grid state.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If state dimensions are invalid.
        """
        required_fields = [
            "timestamp",
            "voltages",
            "voltage_angles",
            "loads",
            "generator_outputs",
            "line_flows",
            "frequency",
        ]

        missing = [f for f in required_fields if f not in data]
        if missing:
            raise KeyError(f"Missing required fields: {missing}")

        return GridState(
            timestamp=data["timestamp"],
            voltages=data["voltages"],
            voltage_angles=data["voltage_angles"],
            loads=data["loads"],
            generator_outputs=data["generator_outputs"],
            line_flows=data["line_flows"],
            frequency=data["frequency"],
            is_faulted=data.get("is_faulted", False),
            fault_info=data.get("fault_info", None),
        )

    def get_voltage_stats(self) -> Dict[str, float]:
        """
        Compute voltage statistics for current state.

        Returns:
            Dict[str, float]: Min, max, mean, and std deviation of voltages.
        """
        import statistics

        return {
            "min": min(self.voltages),
            "max": max(self.voltages),
            "mean": statistics.mean(self.voltages),
            "stdev": statistics.stdev(self.voltages) if len(self.voltages) > 1 else 0.0,
        }

    def get_load_stats(self) -> Dict[str, float]:
        """
        Compute load statistics for current state.

        Returns:
            Dict[str, float]: Min, max, mean, and total loads.
        """
        import statistics

        return {
            "min": min(self.loads),
            "max": max(self.loads),
            "mean": statistics.mean(self.loads),
            "total": sum(self.loads),
        }

    def get_generation_stats(self) -> Dict[str, float]:
        """
        Compute generation statistics for current state.

        Returns:
            Dict[str, float]: Min, max, mean, and total generation.
        """
        import statistics

        return {
            "min": min(self.generator_outputs),
            "max": max(self.generator_outputs),
            "mean": statistics.mean(self.generator_outputs),
            "total": sum(self.generator_outputs),
        }

    def is_stable(self) -> bool:
        """
        Determine if grid is in a stable operating state.

        Returns:
            bool: True if all values are within acceptable ranges.
        """
        voltage_ok = all(
            MIN_VOLTAGE - VOLTAGE_TOLERANCE <= v <= MAX_VOLTAGE + VOLTAGE_TOLERANCE
            for v in self.voltages
        )
        frequency_ok = (
            MIN_FREQUENCY - FREQUENCY_TOLERANCE
            <= self.frequency
            <= MAX_FREQUENCY + FREQUENCY_TOLERANCE
        )
        return voltage_ok and frequency_ok

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"GridState(t={self.timestamp:.1f}s, "
            f"f={self.frequency:.2f}Hz, "
            f"V_avg={sum(self.voltages)/len(self.voltages):.3f}p.u., "
            f"P_total={sum(self.loads):.1f}MW, "
            f"faulted={self.is_faulted})"
        )