CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    severity REAL,
    action_id INTEGER,
    target_bus INTEGER,
    load_reduction_percent REAL,
    explanation TEXT
);