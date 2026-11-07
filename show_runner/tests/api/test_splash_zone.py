from app.main import create_app
from fastapi.testclient import TestClient
from tests.support import PASSWORD, command, get_host


def test_splash_room_queue_undo_and_persistence(tmp_path):
    db = tmp_path / "splash.sqlite3"
    with TestClient(create_app(db, PASSWORD)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        response = client.post(
            "/api/rooms", json={"names": ["A", "B", "C"], "game_type": "splash_zone"}
        )
        assert response.status_code == 201
        s = command(client, response.json(), "start").json()
        assert s["total"] == 8
        original = s
        tokens = s["invites"]
        audience = client.get(
            f"/api/rooms/{s['room_id']}", headers={"x-showdown-view": "audience"}
        ).json()
        assert "answer" not in audience and "all_hints" not in audience
        assert audience["splash_url"] == s["splash_url"]
        s = command(client, s, "buzz", {"question_index": 0}, token=tokens[0]).json()
        # Same-revision simultaneous buzzes must not be lost.
        s = command(client, original, "buzz", {"question_index": 0}, token=tokens[1]).json()
        assert s["active"] == "0" and s["queue"] == ["1"]
        assert s["round_deadline"] is None
        s = command(client, s, "judge", {"correct": False}).json()
        assert s["active"] == "1"
        s = command(client, s, "judge", {"correct": True}).json()
        assert [p["score"] for p in s["players"]] == [-100, 200, 0]
        s = command(client, s, "undo").json()
        assert s["paused"] and s["round_deadline"] is None
        crop, url = s["crop"], s["splash_url"]
    with TestClient(create_app(db, PASSWORD)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        s = get_host(client, s)
        assert s["crop"] == crop and s["splash_url"] == url and s["paused"]
        s = command(client, s, "resume").json()
        assert s["round_deadline"] is None and s["active"] == "1"
        s = command(client, s, "judge", {"correct": False}).json()
        assert s["phase"] == "open" and s["round_deadline"] is not None
