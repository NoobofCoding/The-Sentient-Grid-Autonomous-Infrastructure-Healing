from stable_baselines3 import PPO
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/sentient_grid_ppo")


def evaluate():
    model = PPO.load(MODEL_PATH)

    test_state = np.random.rand(79).astype(np.float32)

    action, _ = model.predict(test_state)

    print("Predicted Action:", action)


if __name__ == "__main__":
    evaluate()