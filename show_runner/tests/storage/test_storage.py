import time

from app.main import create_app
from fastapi.testclient import TestClient
from tests.support import PASSWORD, QUESTIONS, command, get_host, room


def test_undo_and_persistence(tmp_path):
    path = tmp_path / "saved.sqlite3"
    with TestClient(create_app(path, PASSWORD, QUESTIONS)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        s = room(client)
        token = s["invites"][0]
        s = command(client, s, "start").json()
        s = command(client, s, "buzz", token=token).json()
        s = command(client, s, "judge", {"correct": True}).json()
        s = command(client, s, "undo").json()
        assert s["paused"] and s["players"][0]["score"] == 0
        assert s["phase"] == "answering" and s["deadline"] is None
    with TestClient(create_app(path, PASSWORD, QUESTIONS)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        restored = get_host(client, s)
        assert restored["invites"][0] == token and restored["paused"]
        s = command(client, restored, "resume").json()
        assert time.time() < s["deadline"] <= time.time() + 15
        s = command(client, s, "judge", {"correct": True}).json()
        assert s["players"][0]["score"] == 300
