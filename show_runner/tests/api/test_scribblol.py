from app.main import create_app
from fastapi.testclient import TestClient
from tests.support import PASSWORD, command, get_host


def test_drawing_api_privacy_persistence_and_undo(tmp_path):
    db = tmp_path / "drawing.sqlite3"
    with TestClient(create_app(db, PASSWORD)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        response = client.post(
            "/api/rooms", json={"names": ["A", "B", "C"], "game_type": "scribblol"}
        )
        assert response.status_code == 201
        s = command(client, response.json(), "start").json()
        tokens = s["invites"]
        assert s["game_type"] == "scribblol" and s["total"] == 6
        for actor in [1, 2]:
            projection = client.get(
                f"/api/rooms/{s['room_id']}", headers={"Authorization": f"Bearer {tokens[actor]}"}
            ).json()
            assert "answer" not in projection and "all_hints" not in projection
        stroke = {"question_index": 0, "color": "#172d39", "width": 6, "points": [[0, 0], [1, 1]]}
        assert command(client, s, "draw", stroke, token=tokens[1]).status_code == 400
        s = command(client, s, "draw", stroke, token=tokens[0]).json()
        assert len(s["strokes"]) == 1
        s = command(client, s, "buzz", {"question_index": 0}, token=tokens[1]).json()
        s = command(client, s, "judge", {"correct": True}).json()
        assert [p["score"] for p in s["players"]] == [200, 200, 0]
        s = command(client, s, "undo").json()
        assert [p["score"] for p in s["players"]] == [0, 0, 0] and s["paused"]
        assert len(s["strokes"]) == 1
    with TestClient(create_app(db, PASSWORD)) as client:
        client.post("/api/login", json={"password": PASSWORD})
        saved = get_host(client, s)
        assert saved["paused"] and saved["artist"] == "0" and len(saved["strokes"]) == 1
        saved = command(client, saved, "resume").json()
        saved = command(client, saved, "judge", {"correct": True}).json()
        assert [p["score"] for p in saved["players"]] == [200, 200, 0]
