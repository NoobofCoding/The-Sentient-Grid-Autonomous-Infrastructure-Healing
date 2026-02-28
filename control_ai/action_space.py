from shared.action_contracts import ACTION_MAP, action_from_id

def decode_action(action_id: int) -> dict:
    if action_id not in ACTION_MAP:
        raise ValueError("Invalid action_id")

    return action_from_id(action_id)