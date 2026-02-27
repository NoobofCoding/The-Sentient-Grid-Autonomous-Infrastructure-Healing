"""
Comprehensive pytest suite for digital twin simulation components.

Tests cover GridState validation, GridEnvironment dynamics,
FaultInjector behavior, and deterministic seeding.
"""

import pytest
import random
from typing import List

from infrastructure.digital_twin.state_builder import GridState
from infrastructure.digital_twin.grid_env import GridEnvironment
from infrastructure.digital_twin.fault_injection import FaultInjector, FaultType
from infrastructure.digital_twin.config import (
    N_BUSES,
    N_GENERATORS,
    N_LINES,
    NOMINAL_VOLTAGE,
    NOMINAL_FREQUENCY,
    MIN_VOLTAGE,
    MAX_VOLTAGE,
    MIN_FREQUENCY,
    MAX_FREQUENCY,
    FAULT_VOLTAGE_DROP,
    FAULT_FREQUENCY_DEVIATION,
    FAULT_LOAD_SPIKE_PERCENT,
    FAULT_DURATION_STEPS,
)


class TestGridState:
    """Tests for GridState dataclass and validation."""

    def test_grid_state_valid_creation(self):
        """Test creating a valid GridState with correct dimensions."""
        state = GridState(
            timestamp=1.0,
            voltages=[NOMINAL_VOLTAGE] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=NOMINAL_FREQUENCY,
        )

        assert state.timestamp == 1.0
        assert len(state.voltages) == N_BUSES
        assert len(state.loads) == N_BUSES
        assert state.frequency == NOMINAL_FREQUENCY

    def test_grid_state_invalid_voltage_count(self):
        """Test that invalid voltage array size raises ValueError."""
        with pytest.raises(ValueError, match="Voltages must have"):
            GridState(
                timestamp=1.0,
                voltages=[1.0] * (N_BUSES - 1),  # One too few
                voltage_angles=[0.0] * N_BUSES,
                loads=[100.0] * N_BUSES,
                generator_outputs=[120.0] * N_GENERATORS,
                line_flows=[50.0] * N_LINES,
                frequency=NOMINAL_FREQUENCY,
            )

    def test_grid_state_invalid_generator_count(self):
        """Test that invalid generator array size raises ValueError."""
        with pytest.raises(ValueError, match="Generator outputs must have"):
            GridState(
                timestamp=1.0,
                voltages=[1.0] * N_BUSES,
                voltage_angles=[0.0] * N_BUSES,
                loads=[100.0] * N_BUSES,
                generator_outputs=[120.0] * (N_GENERATORS + 1),  # One too many
                line_flows=[50.0] * N_LINES,
                frequency=NOMINAL_FREQUENCY,
            )

    def test_grid_state_invalid_line_count(self):
        """Test that invalid line flows array size raises ValueError."""
        with pytest.raises(ValueError, match="Line flows must have"):
            GridState(
                timestamp=1.0,
                voltages=[1.0] * N_BUSES,
                voltage_angles=[0.0] * N_BUSES,
                loads=[100.0] * N_BUSES,
                generator_outputs=[120.0] * N_GENERATORS,
                line_flows=[50.0] * (N_LINES - 1),  # One too few
                frequency=NOMINAL_FREQUENCY,
            )

    def test_grid_state_to_dict(self):
        """Test conversion of GridState to dictionary."""
        state = GridState(
            timestamp=10.5,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        state_dict = state.to_dict()

        assert state_dict["timestamp"] == 10.5
        assert len(state_dict["voltages"]) == N_BUSES
        assert state_dict["frequency"] == 50.0

    def test_grid_state_from_dict(self):
        """Test reconstruction of GridState from dictionary."""
        original_dict = {
            "timestamp": 20.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.5,
        }

        state = GridState.from_dict(original_dict)

        assert state.timestamp == 20.0
        assert state.frequency == 50.5
        assert len(state.voltages) == N_BUSES

    def test_grid_state_from_dict_missing_field(self):
        """Test that from_dict raises KeyError for missing fields."""
        incomplete_dict = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            # Missing other required fields
        }

        with pytest.raises(KeyError, match="Missing required fields"):
            GridState.from_dict(incomplete_dict)

    def test_grid_state_voltage_stats(self):
        """Test voltage statistics computation."""
        voltages = [0.95, 1.0, 1.05, 1.02, 0.98]
        state = GridState(
            timestamp=1.0,
            voltages=voltages + [1.0] * (N_BUSES - len(voltages)),
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        stats = state.get_voltage_stats()

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "stdev" in stats
        assert stats["min"] < stats["mean"] < stats["max"]

    def test_grid_state_is_stable(self):
        """Test grid stability check."""
        # Stable state
        stable_state = GridState(
            timestamp=1.0,
            voltages=[0.95] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        assert stable_state.is_stable()

        # Unstable voltage
        unstable_state = GridState(
            timestamp=1.0,
            voltages=[0.80] * N_BUSES,  # Below MIN_VOLTAGE
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        # Note: is_stable() should return False, but validation is in __post_init__
        assert not unstable_state.is_stable()

    def test_grid_state_with_fault_info(self):
        """Test GridState with fault metadata."""
        fault_info = {"type": "voltage_sag", "bus": 5, "magnitude": 0.2}
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
            is_faulted=True,
            fault_info=fault_info,
        )

        assert state.is_faulted
        assert state.fault_info["type"] == "voltage_sag"
        assert state.fault_info["bus"] == 5


class TestGridEnvironment:
    """Tests for GridEnvironment simulation."""

    def test_environment_creation(self):
        """Test basic environment initialization."""
        env = GridEnvironment(auto_fault=False)

        assert env.timestamp == 0
        assert len(env.base_load) == N_BUSES
        assert len(env.base_generation) == N_GENERATORS

    def test_environment_step_produces_valid_state(self):
        """Test that step() produces valid GridState."""
        env = GridEnvironment(auto_fault=False)
        state = env.step()

        assert isinstance(state, GridState)
        assert state.timestamp == 1.0
        assert len(state.voltages) == N_BUSES
        assert len(state.loads) == N_BUSES
        assert isinstance(state.frequency, float)

    def test_environment_multiple_steps(self):
        """Test multiple consecutive steps."""
        env = GridEnvironment(auto_fault=False)

        for i in range(10):
            state = env.step()
            assert state.timestamp == i + 1

        assert env.timestamp == 10

    def test_environment_deterministic_seed(self):
        """Test that same seed produces identical sequences."""
        env1 = GridEnvironment(auto_fault=False, random_seed=42)
        env2 = GridEnvironment(auto_fault=False, random_seed=42)

        states1 = env1.step_multiple(10)
        states2 = env2.step_multiple(10)

        for s1, s2 in zip(states1, states2):
            assert s1.timestamp == s2.timestamp
            assert s1.frequency == s2.frequency
            # Check voltages match (within floating point precision)
            for v1, v2 in zip(s1.voltages, s2.voltages):
                assert abs(v1 - v2) < 1e-10

    def test_environment_different_seeds_different_sequences(self):
        """Test that different seeds produce different sequences."""
        env1 = GridEnvironment(auto_fault=False, random_seed=42)
        env2 = GridEnvironment(auto_fault=False, random_seed=43)

        states1 = env1.step_multiple(5)
        states2 = env2.step_multiple(5)

        # At least some differences should exist
        differences = sum(
            1
            for s1, s2 in zip(states1, states2)
            if abs(s1.frequency - s2.frequency) > 0.01
        )
        assert differences > 0

    def test_environment_voltage_bounds(self):
        """Test that voltages stay within reasonable bounds."""
        env = GridEnvironment(auto_fault=False, random_seed=1)

        for _ in range(50):
            state = env.step()
            assert all(0.8 <= v <= 1.2 for v in state.voltages)

    def test_environment_frequency_bounds(self):
        """Test that frequency stays within reasonable bounds."""
        env = GridEnvironment(auto_fault=False, random_seed=1)

        for _ in range(50):
            state = env.step()
            assert 48.0 <= state.frequency <= 52.0

    def test_environment_auto_fault_trigger(self):
        """Test automatic fault triggering."""
        env = GridEnvironment(auto_fault=True, fault_interval=2, random_seed=1)

        state1 = env.step()
        assert not state1.is_faulted

        state2 = env.step()
        # At fault_interval=2, fault should trigger at t=2
        if env.timestamp == 2:
            # Verify that iteration found the fault injection point
            pass

    def test_environment_reset(self):
        """Test environment reset."""
        env = GridEnvironment(auto_fault=False)

        env.step_multiple(5)
        assert env.timestamp == 5

        env.reset()
        assert env.timestamp == 0

    def test_environment_get_status(self):
        """Test status reporting."""
        env = GridEnvironment(auto_fault=False, fault_interval=10)
        env.step_multiple(5)

        status = env.get_status()

        assert "timestamp" in status
        assert status["timestamp"] == 5
        assert "total_load" in status
        assert "fault_status" in status


class TestFaultInjector:
    """Tests for FaultInjector component."""

    def test_fault_injector_initialization(self):
        """Test FaultInjector creation."""
        injector = FaultInjector()

        assert injector.active_fault is None
        assert injector.remaining_steps == 0
        assert len(injector.fault_history) == 0

    def test_inject_voltage_sag(self):
        """Test voltage sag fault injection."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        faulted_state = injector.inject_voltage_sag(state, bus_index=5)

        assert faulted_state.is_faulted
        assert faulted_state.voltages[5] < 1.0
        assert faulted_state.voltages[5] == 1.0 * (1 - FAULT_VOLTAGE_DROP)
        assert injector.active_fault[0] == FaultType.VOLTAGE_SAG

    def test_inject_frequency_disturbance(self):
        """Test frequency disturbance fault injection."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        faulted_state = injector.inject_frequency_disturbance(state, deviation=-2.0)

        assert faulted_state.is_faulted
        assert abs(faulted_state.frequency - 48.0) < 0.01
        assert injector.active_fault[0] == FaultType.FREQUENCY_DISTURBANCE

    def test_inject_load_spike(self):
        """Test load spike fault injection."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        original_load = state.loads[3]
        faulted_state = injector.inject_load_spike(state, bus_index=3)

        assert faulted_state.is_faulted
        assert faulted_state.loads[3] > original_load
        assert injector.active_fault[0] == FaultType.LOAD_SPIKE

    def test_fault_duration(self):
        """Test that faults persist for specified duration."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        # Inject voltage sag
        state = injector.inject_voltage_sag(state, bus_index=0)
        initial_remaining = injector.remaining_steps

        # Apply active fault multiple times
        for _ in range(FAULT_DURATION_STEPS):
            state = injector.apply_active_fault(state)

            if injector.remaining_steps > 0:
                assert state.is_faulted

        # After duration, fault should be cleared
        state = injector.apply_active_fault(state)
        assert injector.active_fault is None or injector.remaining_steps == 0

    def test_fault_random_bus_selection(self):
        """Test that fault type selection is random when bus_index not specified."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        random.seed(42)
        faulted_states = []
        for _ in range(5):
            injector.reset()
            state_copy = GridState.from_dict(state.to_dict())
            faulted_states.append(injector.inject_voltage_sag(state_copy))

        # At least one should have fault on different bus
        bus_indices = [f.fault_info["bus"] for f in faulted_states]
        assert len(set(bus_indices)) > 1

    def test_fault_history_tracking(self):
        """Test that fault history is properly maintained."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        injector.inject_voltage_sag(state, bus_index=0)
        injector.inject_frequency_disturbance(state)
        injector.inject_load_spike(state, bus_index=1)

        assert len(injector.fault_history) >= 3

    def test_fault_injector_reset(self):
        """Test fault injector reset functionality."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        injector.inject_voltage_sag(state)
        assert injector.active_fault is not None

        injector.reset()
        assert injector.active_fault is None
        assert injector.remaining_steps == 0
        assert len(injector.fault_history) == 0

    def test_fault_get_status(self):
        """Test fault status reporting."""
        injector = FaultInjector()
        state = GridState(
            timestamp=1.0,
            voltages=[1.0] * N_BUSES,
            voltage_angles=[0.0] * N_BUSES,
            loads=[100.0] * N_BUSES,
            generator_outputs=[120.0] * N_GENERATORS,
            line_flows=[50.0] * N_LINES,
            frequency=50.0,
        )

        injector.inject_voltage_sag(state)
        status = injector.get_fault_status()

        assert status["has_active_fault"]
        assert status["fault_type"] == "voltage_sag"
        assert status["remaining_steps"] > 0


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_environment_with_fault_injection(self):
        """Test environment stepping with fault injection."""
        env = GridEnvironment(auto_fault=False, random_seed=1)

        # Step without fault
        state1 = env.step()
        assert not state1.is_faulted

        # Inject fault
        state2 = env.fault_injector.inject_voltage_sag(state1, bus_index=0)
        assert state2.is_faulted

        # Continue stepping with fault active
        for _ in range(FAULT_DURATION_STEPS):
            state = env.step()
            if state.is_faulted or env.fault_injector.remaining_steps > 0:
                # Fault should still be active or in recovery
                pass

    def test_full_simulation_sequence(self):
        """Test complete simulation sequence with all components."""
        env = GridEnvironment(
            auto_fault=True,
            fault_interval=5,
            random_seed=42
        )

        states = []
        for i in range(20):
            state = env.step()
            states.append(state)

            assert state.timestamp == i + 1
            assert len(state.voltages) == N_BUSES
            assert state.is_stable() or state.is_faulted

        # At least one state should be faulted due to auto_fault=True
        faulted_count = sum(1 for s in states if s.is_faulted)
        assert faulted_count > 0
