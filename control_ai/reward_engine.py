import numpy as np

def calculate_reward(prev_state, current_state, action_dict):

    voltages = np.array(current_state["voltages"])
    severity = current_state["severity_score"]

    # Voltage deviation penalty
    voltage_deviation = np.mean(np.abs(voltages - 1.0))

    voltage_penalty = voltage_deviation * 5

    # Heavy penalty if any voltage below 0.90
    critical_penalty = np.sum(voltages < 0.90) * 10

    # Penalize large load shedding
    action_penalty = action_dict["load_reduction_percent"] * 2

    # Reward recovery
    recovery_bonus = (1.0 - severity) * 5

    reward = (
        recovery_bonus
        - voltage_penalty
        - critical_penalty
        - action_penalty
    )

    return float(reward)