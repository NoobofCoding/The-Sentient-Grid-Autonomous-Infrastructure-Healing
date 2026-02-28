PPO_CONFIG = {
    "learning_rate": 3e-4,
    "gamma": 0.99,
    "n_steps": 2048,
    "batch_size": 64,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "verbose": 1
}

POLICY_CONFIG = {
    "net_arch": [256, 256],
    "activation_fn": "tanh"
}