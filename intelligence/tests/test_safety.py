from intelligence.safety.safety_filter import SafetyFilter

def test_safety_cap():
    sf = SafetyFilter()

    action = {
        "action_id": 1,
        "target_bus": 5,
        "load_reduction_percent": 0.8
    }

    grid_state = {"frequency": 50.0}

    validated = sf.validate(action, grid_state)

    assert validated["load_reduction_percent"] <= 0.30