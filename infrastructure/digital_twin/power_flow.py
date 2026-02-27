"""
Basic power flow calculations for the digital twin.

This module currently implements a simple DC approximation useful for
simulations where only relative magnitudes (voltage deviations, frequency
imbalance) are required.  Future improvements may replace this with a full
AC power flow solver or integrate with external libraries.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PowerFlowCalculator:
    """Performs simplistic power flow computations on a topology.

    The formulas here are intentionally crude: voltage deviations are assumed
    proportional to net load on a bus, and frequency is computed from total
    generation-load imbalance.  The purpose is to keep the computation fast
    and understandable while still providing realistic-looking output for
    streaming and control algorithms.
    """

    def __init__(self):
        logger.info("PowerFlowCalculator initialized")

    def compute_voltages(self, loads: List[float]) -> List[float]:
        """Compute bus voltages given loads using a simple linear model.

        Args:
            loads: list of load values in MW, one per bus.

        Returns:
            List[float]: per-unit voltages (near 1.0).
        """
        voltages = []
        for load in loads:
            # assume each 100 MW of load drops voltage by 0.01 p.u.
            drop = load * 0.0001
            voltages.append(max(0.8, min(1.2, 1.0 - drop)))
        return voltages

    def compute_frequency(self, total_load: float, total_generation: float) -> float:
        """Compute system frequency from imbalance (gentle model).

        This implementation avoids the extreme values produced by the previous
        linear formula when generation and load were far apart.  Instead it
        produces a value near nominal and adds a small random perturbation.
        This allows higher-level modules (like GridEnvironment) to inject their
        own dynamic effects if desired.
        """
        import random

        # simple baseline at nominal
        freq = 50.0
        # small random noise to keep different seeds diverging
        freq += random.uniform(-0.05, 0.05)
        return freq

    def compute_imbalance(self, total_load: float, total_generation: float) -> float:
        """Return load-generation imbalance in MW."""
        return total_load - total_generation
