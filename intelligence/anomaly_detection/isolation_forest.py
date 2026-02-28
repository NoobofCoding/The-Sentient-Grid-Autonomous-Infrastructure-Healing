import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        self.is_trained = False

    def train(self, historical_data: np.ndarray):
        self.model.fit(historical_data)
        self.is_trained = True

    def score(self, state_vector: np.ndarray) -> float:
        if not self.is_trained:
            return 0.0
        return float(-self.model.decision_function([state_vector])[0])