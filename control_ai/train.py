import gymnasium as gym
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gymnasium import spaces
from reward_engine import calculate_reward
from action_space import decode_action
from ppo_config import PPO_CONFIG
from observation_builder import build_observation_from_state, OBSERVATION_DIM

# IMPORT digital twin (pillar 1)
from infrastructure.digital_twin.grid_env import GridEnvironment
from stable_baselines3 import PPO


class GridEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.grid = GridEnvironment()

        self.action_space = spaces.Discrete(4)

        # 39 voltages + 39 loads + 1 frequency
        self.state_dim = OBSERVATION_DIM

        low = np.array(([0.0] * 39) + ([0.0] * 39) + [45.0], dtype=np.float32)
        high = np.array(([2.0] * 39) + ([2000.0] * 39) + [55.0], dtype=np.float32)

        self.observation_space = spaces.Box(
            low=low,
            high=high,
            shape=(self.state_dim,),
            dtype=np.float32
        )

        self.prev_state = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.grid.reset(random_seed=seed)
        grid_state = self._normalize_state(self.grid.step())

        state_vector = build_observation_from_state(grid_state)

        self.prev_state = grid_state

        return state_vector, {}

    def step(self, action_id):

        action_dict = decode_action(int(action_id))

        # Advance digital twin by one simulation step.
        grid_state = self._normalize_state(self.grid.step())

        state_vector = build_observation_from_state(grid_state)

        reward = calculate_reward(
            self.prev_state,
            grid_state,
            action_dict
        )

        self.prev_state = grid_state

        terminated = False
        truncated = False

        return state_vector, reward, terminated, truncated, {}

    def _normalize_state(self, grid_state):
        if hasattr(grid_state, "to_dict"):
            state = grid_state.to_dict()
        else:
            state = dict(grid_state)

        if "severity_score" not in state:
            voltages = np.asarray(state["voltages"], dtype=np.float32)
            state["severity_score"] = float(np.mean(np.abs(voltages - 1.0)))

        return state


def train_model(total_timesteps: int = 50_000) -> Path:
    env = GridEnv()
    model = PPO("MlpPolicy", env, **PPO_CONFIG)
    model.learn(total_timesteps=total_timesteps)

    model_path = Path(__file__).resolve().parent / "models" / "sentient_grid_ppo.zip"
    model.save(str(model_path.with_suffix("")))
    return model_path


if __name__ == "__main__":
    output_path = train_model()
    print(f"Model saved to: {output_path}")