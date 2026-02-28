"""
Shared action contracts for Control AI -> Infrastructure messaging.
"""

from __future__ import annotations

from typing import Dict, Any
import math


ACTION_MAP = {
	0: "NO_OP",
	1: "REDUCE_LOAD_10",
	2: "REDUCE_LOAD_15",
	3: "REDISTRIBUTE",
}


ACTION_DEFINITIONS: Dict[int, Dict[str, Any]] = {
	0: {"target_bus": None, "load_reduction_percent": 0.0},
	1: {"target_bus": 5, "load_reduction_percent": 0.10},
	2: {"target_bus": 15, "load_reduction_percent": 0.15},
	3: {"target_bus": 22, "load_reduction_percent": 0.05},
}


def action_from_id(action_id: int) -> Dict[str, Any]:
	"""
	Convert an action id into the structured action payload contract.

	Args:
		action_id: Discrete policy output id.

	Returns:
		Structured action dict with required contract fields.

	Raises:
		ValueError: If action_id is not defined.
	"""
	if action_id not in ACTION_DEFINITIONS:
		raise ValueError(f"Unknown action_id: {action_id}")

	action = ACTION_DEFINITIONS[action_id]
	return {
		"action_id": action_id,
		"target_bus": action["target_bus"],
		"load_reduction_percent": float(action["load_reduction_percent"]),
	}


def validate_action_payload(action_payload: Dict[str, Any]) -> None:
	"""
	Validate action payload against shared action contract.

	Raises:
		ValueError: if payload violates contract.
	"""
	required_fields = {"action_id", "target_bus", "load_reduction_percent", "model_version"}
	missing = [field for field in required_fields if field not in action_payload]
	if missing:
		raise ValueError(f"Action payload missing fields: {missing}")

	action_id = action_payload["action_id"]
	if not isinstance(action_id, int):
		raise ValueError(f"action_id must be int, got {type(action_id).__name__}")

	if action_id not in ACTION_DEFINITIONS:
		raise ValueError(f"Unknown action_id: {action_id}")

	expected = action_from_id(action_id)
	target_bus = action_payload["target_bus"]
	if target_bus != expected["target_bus"]:
		raise ValueError(
			f"target_bus mismatch for action_id={action_id}: "
			f"expected {expected['target_bus']}, got {target_bus}"
		)

	load_reduction = action_payload["load_reduction_percent"]
	if not isinstance(load_reduction, (int, float)):
		raise ValueError(
			"load_reduction_percent must be numeric, "
			f"got {type(load_reduction).__name__}"
		)

	if not math.isclose(float(load_reduction), expected["load_reduction_percent"], rel_tol=0.0, abs_tol=1e-8):
		raise ValueError(
			f"load_reduction_percent mismatch for action_id={action_id}: "
			f"expected {expected['load_reduction_percent']}, got {load_reduction}"
		)

	if not isinstance(action_payload["model_version"], str) or not action_payload["model_version"]:
		raise ValueError("model_version must be a non-empty string")

