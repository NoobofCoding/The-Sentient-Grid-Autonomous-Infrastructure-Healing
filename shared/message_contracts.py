"""
Shared message contract helpers.
"""

from __future__ import annotations

from typing import Any, Dict, List


def infer_disturbance_type(state: Dict[str, Any], severity_score: float) -> str:
	"""
	Infer disturbance type for analytics and downstream reporting.
	"""
	fault_info = state.get("fault_info")
	if isinstance(fault_info, dict) and fault_info.get("type"):
		return str(fault_info["type"])

	if bool(state.get("is_faulted", False)):
		return "faulted"

	if severity_score >= 0.7:
		return "critical_anomaly"

	if severity_score >= 0.5:
		return "moderate_anomaly"

	return "normal"


def build_pillar4_payload(
	*,
	timestamp: int | float,
	bus_voltages: List[float],
	load_levels: List[float],
	disturbance_type: str,
	rl_action: Dict[str, Any],
	safety_override_flag: bool,
	reward: float,
	stability_status: str,
) -> Dict[str, Any]:
	"""
	Build analytics payload for Pillar 4 in the required schema.
	"""
	return {
		"timestamp": timestamp,
		"bus_voltages": bus_voltages,
		"load_levels": load_levels,
		"disturbance_type": disturbance_type,
		"rl_action": rl_action,
		"safety_override_flag": bool(safety_override_flag),
		"reward": float(reward),
		"stability_status": stability_status,
	}


def validate_pillar4_payload(payload: Dict[str, Any]) -> None:
	"""
	Validate required keys and value types for Pillar 4 payload.
	"""
	required = {
		"timestamp",
		"bus_voltages",
		"load_levels",
		"disturbance_type",
		"rl_action",
		"safety_override_flag",
		"reward",
		"stability_status",
	}
	missing = [key for key in required if key not in payload]
	if missing:
		raise ValueError(f"Pillar 4 payload missing fields: {missing}")

	if not isinstance(payload["bus_voltages"], list):
		raise ValueError("bus_voltages must be a list")

	if not isinstance(payload["load_levels"], list):
		raise ValueError("load_levels must be a list")

	if not isinstance(payload["disturbance_type"], str):
		raise ValueError("disturbance_type must be a string")

	if not isinstance(payload["rl_action"], dict):
		raise ValueError("rl_action must be an object")

	if not isinstance(payload["safety_override_flag"], bool):
		raise ValueError("safety_override_flag must be boolean")

	if not isinstance(payload["reward"], (int, float)):
		raise ValueError("reward must be numeric")

	if not isinstance(payload["stability_status"], str):
		raise ValueError("stability_status must be a string")
