"""Lightweight schema validation helpers for prototype runtime."""

from __future__ import annotations

import json
from typing import Any, Dict

from shared.action_contracts import validate_action_payload
from shared.message_contracts import validate_pillar4_payload


class SchemaValidationError(ValueError):
	"""Raised when a payload fails schema or contract validation."""


def validate_grid_state_message(payload: Dict[str, Any]) -> None:
	required = {"timestamp", "voltages", "loads", "frequency"}
	missing = [key for key in required if key not in payload]
	if missing:
		raise SchemaValidationError(f"Grid state schema mismatch: missing {missing}")

	if not isinstance(payload.get("voltages"), list):
		raise SchemaValidationError("Grid state schema mismatch: voltages must be a list")
	if not isinstance(payload.get("loads"), list):
		raise SchemaValidationError("Grid state schema mismatch: loads must be a list")
	if not isinstance(payload.get("frequency"), (int, float)):
		raise SchemaValidationError("Grid state schema mismatch: frequency must be numeric")


def validate_control_action_message(payload: Dict[str, Any]) -> None:
	try:
		validate_action_payload(payload)
	except Exception as exc:
		raise SchemaValidationError(f"Control action contract mismatch: {exc}") from exc


def validate_pillar4_analytics_message(payload: Dict[str, Any]) -> None:
	try:
		validate_pillar4_payload(payload)
	except Exception as exc:
		raise SchemaValidationError(f"Pillar 4 analytics contract mismatch: {exc}") from exc


def decode_and_validate_json(raw_payload: bytes | str | Dict[str, Any]) -> Dict[str, Any]:
	"""
	Decode payload into dict and validate as grid state message.
	"""
	if isinstance(raw_payload, dict):
		payload = raw_payload
	elif isinstance(raw_payload, bytes):
		payload = json.loads(raw_payload.decode("utf-8"))
	elif isinstance(raw_payload, str):
		payload = json.loads(raw_payload)
	else:
		raise SchemaValidationError(f"Unsupported payload type: {type(raw_payload).__name__}")

	if not isinstance(payload, dict):
		raise SchemaValidationError("Decoded payload must be a JSON object")

	validate_grid_state_message(payload)
	return payload
