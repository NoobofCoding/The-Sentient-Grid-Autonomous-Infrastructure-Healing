"""
Configuration module for IEEE-39 Bus Digital Twin Simulation.

This module centralized all constants and configuration parameters for the power grid
digital twin, ensuring consistency across all simulation components.
"""

from typing import Final

# ============================================================================
# IEEE-39 Bus System Parameters (New England 39-Bus System)
# ============================================================================

N_BUSES: Final[int] = 39
"""Total number of buses in the IEEE 39-bus system."""

N_GENERATORS: Final[int] = 10
"""Total number of generators in the system."""

N_LINES: Final[int] = 46
"""Total number of transmission lines in the system."""

# ============================================================================
# Simulation Timing Configuration
# ============================================================================

SIMULATION_STEP_SECONDS: Final[float] = 1.0
"""Duration of each simulation step in seconds."""

# Backwards-compatible alias requested by specification
SIM_STEP_SEC: Final[float] = SIMULATION_STEP_SECONDS
"""Duration of each simulation step in seconds (alias `SIM_STEP_SEC`)."""

SIMULATION_STEP_MILLISECONDS: Final[int] = int(SIMULATION_STEP_SECONDS * 1000)
"""Duration of each simulation step in milliseconds."""

# ============================================================================
# Nominal Electrical Values
# ============================================================================

NOMINAL_VOLTAGE: Final[float] = 1.0
"""Nominal voltage in per-unit (p.u.). Reference is 100 kV base."""

NOMINAL_FREQUENCY: Final[float] = 50.0
"""Nominal system frequency in Hz."""

NOMINAL_VOLTAGE_BASE_KV: Final[float] = 100.0
"""Base voltage for per-unit conversion in kV."""

# ============================================================================
# Operating Bounds (Safe Operating Region)
# ============================================================================

MIN_VOLTAGE: Final[float] = 0.90
"""Minimum acceptable voltage in p.u. Below this triggers alerts."""

MAX_VOLTAGE: Final[float] = 1.10
"""Maximum acceptable voltage in p.u. Above this triggers alerts."""

MIN_FREQUENCY: Final[float] = 49.0
"""Minimum acceptable frequency in Hz. Below this is critical."""

MAX_FREQUENCY: Final[float] = 51.0
"""Maximum acceptable frequency in Hz. Above this is critical."""

# ============================================================================
# Load and Generation Parameters
# ============================================================================

BASE_LOAD_MW: Final[float] = 100.0
"""Base load per bus in MW for nominal conditions."""

BASE_GENERATION_MW: Final[float] = 120.0
"""Base generation per generator in MW for nominal conditions."""

MAX_LOAD_VARIATION_PERCENT: Final[float] = 0.10
"""Maximum load variation as percentage of base load (10%)."""

LOAD_RAMP_RATE: Final[float] = 5.0
"""Load ramp rate in MW per simulation step for smooth transitions."""

# ============================================================================
# Voltage Simulation Parameters
# ============================================================================

VOLTAGE_PROPORTIONAL_DROP: Final[float] = 0.0001
"""Proportional voltage drop per MW of load (0.01% per 100 MW)."""

VOLTAGE_RANDOM_NOISE: Final[float] = 0.01
"""Random voltage noise amplitude in p.u. (±0.5%)."""

# ============================================================================
# Frequency Simulation Parameters
# ============================================================================

FREQUENCY_LOAD_SENSITIVITY: Final[float] = 0.00001
"""Frequency change per MW load-generation imbalance (Hz/MW)."""

FREQUENCY_DAMPING: Final[float] = 0.05
"""Frequency damping factor to smooth frequency variations."""

FREQUENCY_RANDOM_NOISE: Final[float] = 0.05
"""Random frequency noise amplitude in Hz (±0.05 Hz)."""

# ============================================================================
# Line Flow Simulation Parameters
# ============================================================================

AVERAGE_LINE_FLOW_MULTIPLIER: Final[float] = 0.5
"""Multiplier for average line flow relative to total load (50%)."""

LINE_FLOW_RANDOM_VARIATION: Final[float] = 5.0
"""Random variation in line flow in MW (±5 MW)."""

# ============================================================================
# Voltage Angle Simulation Parameters
# ============================================================================

MAX_VOLTAGE_ANGLE_DEGREES: Final[float] = 5.0
"""Maximum voltage angle deviation in degrees (±5°)."""

# ============================================================================
# Fault Injection Parameters
# ============================================================================

# Voltage Sag Fault
FAULT_VOLTAGE_DROP: Final[float] = 0.20
"""Voltage drop magnitude for voltage sag fault (20% from nominal)."""

# Frequency Disturbance Fault
FAULT_FREQUENCY_DEVIATION: Final[float] = 2.0
"""Frequency deviation magnitude for frequency disturbance fault (±2 Hz)."""

# Load Spike Fault
FAULT_LOAD_SPIKE_PERCENT: Final[float] = 0.30
"""Load increase percentage for load spike fault (30%)."""

# General Fault Parameters
FAULT_DURATION_STEPS: Final[int] = 5
"""Duration of fault in simulation steps (5 steps = 5 seconds)."""

FAULT_RECOVERY_STEPS: Final[int] = 3
"""Steps required for system to smoothly recover from fault."""

# ============================================================================
# Logging and Monitoring Configuration
# ============================================================================

LOG_LEVEL: Final[str] = "INFO"
"""Default logging level for the system."""

LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Standard log format for all modules."""

# ============================================================================
# Validation Tolerances
# ============================================================================

VOLTAGE_TOLERANCE: Final[float] = 0.001
"""Tolerance for voltage validation in p.u. (±0.1%)."""

FREQUENCY_TOLERANCE: Final[float] = 0.01
"""Tolerance for frequency validation in Hz (±0.01 Hz)."""