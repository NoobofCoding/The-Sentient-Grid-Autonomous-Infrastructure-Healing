# infrastructure/tests/test_power_flow.py

import pytest

from infrastructure.digital_twin.state_builder import GridState
from infrastructure.digital_twin.grid_env import GridEnvironment
from infrastructure.digital_twin.config import (
    N_BUSES,
    N_GENERATORS,
    N_LINES
)
from infrastructure.digital_twin.grid_topology import GridTopology
from infrastructure.digital_twin.power_flow import PowerFlowCalculator
from infrastructure.streaming import stream_config


def test_grid_state_dimensions():
    state = GridState(
        timestamp=1,
        voltages=[1.0] * N_BUSES,
        voltage_angles=[0.0] * N_BUSES,
        loads=[100.0] * N_BUSES,
        generator_outputs=[120.0] * N_GENERATORS,
        line_flows=[50.0] * N_LINES,
        frequency=50.0,
    )

    assert len(state.voltages) == N_BUSES
    assert len(state.voltage_angles) == N_BUSES
    assert len(state.loads) == N_BUSES
    assert len(state.generator_outputs) == N_GENERATORS
    assert len(state.line_flows) == N_LINES


def test_environment_step_produces_valid_state():
    env = GridEnvironment(auto_fault=False)
    state = env.step()

    assert state.timestamp == 1
    assert len(state.voltages) == N_BUSES
    assert len(state.loads) == N_BUSES
    assert isinstance(state.frequency, float)


def test_topology_default():
    topo = GridTopology.default()
    assert len(topo.buses) >= 1
    assert topo.get_bus_info(0).id == 0


def test_power_flow_simple():
    pf = PowerFlowCalculator()
    voltages = pf.compute_voltages([50.0, 60.0])
    assert all(0.8 <= v <= 1.2 for v in voltages)
    freq = pf.compute_frequency(110.0, 120.0)
    assert 48.0 <= freq <= 52.0


def test_stream_config_values():
    assert hasattr(stream_config, "KAFKA_BOOTSTRAP_SERVERS")
    assert hasattr(stream_config, "STREAM_INTERVAL_SEC")


def test_fault_injection_changes_voltage():
    env = GridEnvironment(auto_fault=False)
    state = env.step()

    original_voltage = state.voltages[0]

    faulty_state = env.fault_injector.inject_voltage_sag(state, bus_index=0)

    assert faulty_state.voltages[0] < original_voltage


def test_auto_fault_trigger():
    env = GridEnvironment(auto_fault=True, fault_interval=1)

    state1 = env.step()
    state2 = env.step()

    # At least one bus voltage should drop below nominal
    assert any(v < 1.0 for v in state2.voltages)