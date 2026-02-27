"""
Grid topology definitions for the digital twin.

Provides lightweight representations of buses, generators, loads, and lines
along with a simple default topology suitable for simulation and testing.
Other modules (e.g. environment, power flow, control AI) can import this
information without requiring the entire simulation engine.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Bus:
    """Represents a power system bus (node)."""
    id: int
    name: str
    voltage_base: float = 1.0  # per-unit


@dataclass
class Generator:
    """Represents a generator connected to a bus."""
    id: int
    bus_id: int
    max_mw: float
    min_mw: float


@dataclass
class Load:
    """Represents a load attached to a bus."""
    id: int
    bus_id: int
    mw: float


@dataclass
class Line:
    """Represents a transmission line between two buses."""
    id: int
    from_bus: int
    to_bus: int
    max_mw: float


class GridTopology:
    """Container for the system topology with utility accessors."""

    def __init__(self, buses: List[Bus], generators: List[Generator], loads: List[Load], lines: List[Line]):
        self.buses = buses
        self.generators = generators
        self.loads = loads
        self.lines = lines

    @classmethod
    def default(cls) -> "GridTopology":
        """Return a very small default network for demonstrations/testing."""
        buses = [Bus(id=i, name=f"Bus{i}") for i in range(3)]
        generators = [Generator(id=0, bus_id=0, max_mw=100.0, min_mw=10.0)]
        loads = [Load(id=i, bus_id=i, mw=50.0) for i in range(3)]
        lines = [Line(id=0, from_bus=0, to_bus=1, max_mw=80.0), Line(id=1, from_bus=1, to_bus=2, max_mw=80.0)]
        return cls(buses, generators, loads, lines)

    def get_bus_info(self, bus_id: int) -> Bus:
        """Lookup bus information by id."""
        for bus in self.buses:
            if bus.id == bus_id:
                return bus
        raise KeyError(f"Bus {bus_id} not found")

    def get_generator_info(self, gen_id: int) -> Generator:
        """Lookup generator information by id."""
        for gen in self.generators:
            if gen.id == gen_id:
                return gen
        raise KeyError(f"Generator {gen_id} not found")

    def get_load_info(self, load_id: int) -> Load:
        """Lookup load information by id."""
        for load in self.loads:
            if load.id == load_id:
                return load
        raise KeyError(f"Load {load_id} not found")
