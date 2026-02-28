"""
Kafka topic names used throughout the sentient-grid system.

Centralizes topic naming to ensure consistency across all producers
and consumers throughout the distributed system.
"""

# Grid State Streaming
GRID_STATE_TOPIC: str = "grid.state.stream"
"""Topic for publishing grid state snapshots from digital twin."""

GRID_STATE_ALERTS_TOPIC: str = "grid.alerts.critical"
"""Topic for publishing critical grid alerts and anomalies."""

# Fault Events
FAULT_EVENTS_TOPIC: str = "grid.faults.injected"
"""Topic for publishing fault injection events."""

FAULT_RECOVERY_TOPIC: str = "grid.faults.recovery"
"""Topic for publishing fault recovery events."""

# Control Signals
CONTROL_ACTIONS_TOPIC: str = "grid.control.actions"
"""Topic for publishing AI control actions to the grid."""

GRID_ACTION_TOPIC: str = CONTROL_ACTIONS_TOPIC
"""Backward-compatible alias for control actions topic."""

GRID_CONTROL_TOPIC: str = CONTROL_ACTIONS_TOPIC
"""Compatibility alias for control topic naming across pillars."""

# Analytics and Logging
ANALYTICS_TOPIC: str = "grid.analytics.metrics"
"""Topic for publishing analytics and computed metrics."""

AUDIT_LOG_TOPIC: str = "grid.audit.log"
"""Topic for compliance and audit logging."""

# Anomaly Detection
ANOMALY_DETECTION_TOPIC: str = "grid.anomalies.detected"
"""Topic for publishing detected anomalies from intelligence module."""

GRID_ANOMALY_TOPIC: str = ANOMALY_DETECTION_TOPIC
"""Compatibility alias for anomaly topic naming across pillars."""

# System Health
SYSTEM_HEALTH_TOPIC: str = "grid.system.health"
"""Topic for publishing system health status and metrics."""