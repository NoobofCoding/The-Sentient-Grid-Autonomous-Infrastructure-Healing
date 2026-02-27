import sqlite3
from pathlib import Path


class AuditStorage:
    def __init__(self, db_path="audit.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        schema_path = Path(__file__).resolve().parent / "database_schema.sql"
        if schema_path.exists():
            sql = schema_path.read_text(encoding="utf-8")
            self.cursor.executescript(sql)
            self.conn.commit()

    def store_event(self, event_data: dict):
        self.cursor.execute("""
            INSERT INTO events
            (timestamp, severity, action_id, target_bus,
             load_reduction_percent, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_data["timestamp"],
            event_data["severity"],
            event_data["action_id"],
            event_data["target_bus"],
            event_data["load_reduction_percent"],
            event_data["explanation"]
        ))
        self.conn.commit()