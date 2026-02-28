import torch
import torch.nn as nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=64):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, batch_first=True)

    def forward(self, x):
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return decoded


class LSTMDetector:
    def __init__(self, input_dim):
        self.model = LSTMAutoencoder(input_dim)
        self.criterion = nn.MSELoss()

    def score(self, sequence_tensor):
        with torch.no_grad():
            reconstruction = self.model(sequence_tensor)
            loss = self.criterion(reconstruction, sequence_tensor)
        return float(loss.item())