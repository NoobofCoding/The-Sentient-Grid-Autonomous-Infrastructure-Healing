import numpy as np

def build_state_vector(message: dict) -> np.ndarray:
    return np.array(
        message["voltages"]
        + message["loads"]
        + [message["frequency"]]
    )