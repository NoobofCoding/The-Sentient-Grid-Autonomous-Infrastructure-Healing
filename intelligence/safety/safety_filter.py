from .constraint_rules import cap_load_reduction
from .stability_checker import is_frequency_safe
from .fallback_mechanism import fallback_action


class SafetyFilter:
    def validate(self, action: dict, grid_state: dict) -> dict:
        if not is_frequency_safe(grid_state["frequency"]):
            return fallback_action()

        action["load_reduction_percent"] = cap_load_reduction(
            action["load_reduction_percent"]
        )

        return action