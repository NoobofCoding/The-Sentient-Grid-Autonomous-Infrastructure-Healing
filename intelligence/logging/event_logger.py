from .audit_storage import AuditStorage


class EventLogger:
    def __init__(self):
        self.storage = AuditStorage()

    def log(self, event_data: dict):
        self.storage.store_event(event_data)