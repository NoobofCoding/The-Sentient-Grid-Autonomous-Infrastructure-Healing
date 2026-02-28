def normalize(value, max_val=1.0):
    return max(0.0, min(value / max_val, 1.0))


def compute_severity(iso_score: float, lstm_score: float) -> float:
    iso_norm = normalize(iso_score)
    lstm_norm = normalize(lstm_score)

    severity = 0.6 * iso_norm + 0.4 * lstm_norm
    return round(severity, 4)