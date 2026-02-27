from intelligence.anomaly_detection.detector_service import AnomalyDetectionService


def test_severity_output():
    message = {
        "voltages": [1.0] * 4,
        "loads": [100] * 4,
        "frequency": 50.0,
        "line_flows": []
    }

    feature_count = len(message["voltages"]) + len(message["loads"]) + 1
    service = AnomalyDetectionService(input_dim=feature_count)

    result = service.process(message)

    assert "severity_score" in result