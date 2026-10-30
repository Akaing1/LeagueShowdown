import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        self.connection.commit()

    def all(self):
        return {
            room_id: json.loads(data)
            for room_id, data in self.connection.execute("SELECT id, data FROM rooms")
        }

    def save(self, room):
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO rooms VALUES (?, ?)", (room["id"], json.dumps(room))
            )

    def close(self):
        self.connection.close()
