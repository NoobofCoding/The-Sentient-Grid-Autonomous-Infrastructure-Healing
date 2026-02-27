import torch
from .feature_engineering import build_state_vector
from .isolation_forest import IsolationForestDetector
from .lstm_autoencoder import LSTMDetector
from .severity_scoring import compute_severity


class AnomalyDetectionService:
    def __init__(self, input_dim):
        self.if_detector = IsolationForestDetector()
        self.lstm_detector = LSTMDetector(input_dim)

    def process(self, message: dict) -> dict:
        state_vector = build_state_vector(message)

        iso_score = self.if_detector.score(state_vector)

        lstm_input = torch.tensor(
            state_vector.reshape(1, 1, -1)
        ).float()

        lstm_score = self.lstm_detector.score(lstm_input)

        severity = compute_severity(iso_score, lstm_score)

        return {
            "voltages": message["voltages"],
            "loads": message["loads"],
            "severity_score": severity
        }