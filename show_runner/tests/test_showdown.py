import time
import uuid
from copy import deepcopy

import pytest
from app import engine
from app.main import create_app
from fastapi.testclient import TestClient

PASSWORD = "private-host-password-for-tests"
QUESTIONS = [
    {
        "answer": "Ahri",
        "hints": ["First clue", "Second clue", "Third clue"],
        "points": [300, 200, 100],
    },
    {"answer": "Braum", "hints": ["Another clue"], "points": [100]},
]


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "test.sqlite3", PASSWORD, QUESTIONS)) as c:
        assert c.post("/api/login", json={"password": PASSWORD}).status_code == 200
        yield c


def room(client):
    response = client.post("/api/rooms", json={"names": ["Rat", "Meinya", "Minami"]})
    assert response.status_code == 201
    return response.json()


def command(client, state, action, payload=None, token=None, command_id=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(
        f"/api/rooms/{state['room_id']}/commands",
        headers=headers,
        json={
            "id": command_id or str(uuid.uuid4()),
            "revision": state["revision"],
            "action": action,
            "payload": payload or {},
        },
    )


def get_host(client, state):
    return client.get(f"/api/rooms/{state['room_id']}").json()


def test_three_seats_and_host_auth(client):
    assert client.post("/api/rooms", json={"names": ["One", "Two"]}).status_code == 422
    assert client.post("/api/rooms", json={"names": ["Rat", "rat", "Other"]}).status_code == 422
    client.cookies.clear()
    assert client.post("/api/rooms", json={"names": ["One", "Two", "Three"]}).status_code == 401
    assert client.get("/api/rooms").status_code == 401
    for _ in range(10):
        assert client.post("/api/login", json={"password": "wrong"}).status_code == 401
    assert client.post("/api/login", json={"password": PASSWORD}).status_code == 429


def test_full_game_and_private_projections(client):
    s = room(client)
    tokens = s["invites"]
    s = command(client, s, "start").json()
    assert s["answer"] == "Ahri" and s["hints"] == ["First clue"]
    # Broadcast mode stays public even in the host's signed-in browser.
    public = client.get(
        f"/api/rooms/{s['room_id']}", headers={"X-Showdown-View": "audience"}
    ).json()
    assert "answer" not in public and "all_hints" not in public and "invites" not in public
    client.cookies.clear()
    audience = client.get(f"/api/rooms/{s['room_id']}").json()
    assert "answer" not in audience and "Second clue" not in str(audience)
    assert command(client, s, "open").status_code == 403
    assert command(client, s, "open", token=tokens[0]).status_code == 400
    assert command(client, s, "buzz", token="invalid").status_code == 403
    client.post("/api/login", json={"password": PASSWORD})
    s = get_host(client, s)
    s = command(client, s, "buzz", token=tokens[0]).json()
    assert s["active"] == "0" and "answer" not in s
    # The losing near-simultaneous buzz never takes over or changes scores.
    assert command(client, s, "buzz", token=tokens[1]).status_code == 400
    assert (
        command(client, s, "submit_answer", {"answer": "Ahri"}, token=tokens[1]).status_code == 400
    )
    s = command(client, s, "submit_answer", {"answer": "Ahri"}, token=tokens[0]).json()
    assert s["phase"] == "judging"
    assert (
        "submission"
        not in client.get(
            f"/api/rooms/{s['room_id']}", headers={"X-Showdown-View": "audience"}
        ).json()
    )
    s = command(client, s, "judge", {"correct": True}).json()
    assert s["players"][0]["score"] == 300 and s["phase"] == "revealed"
    public = client.get(
        f"/api/rooms/{s['room_id']}", headers={"X-Showdown-View": "audience"}
    ).json()
    assert public["answer"] == "Ahri" and "invites" not in public
    assert command(client, s, "judge", {"correct": True}).status_code == 400
    s = command(client, s, "next").json()
    s = command(client, s, "reveal").json()
    s = command(client, s, "next").json()
    assert s["phase"] == "finished" and s["players"][0]["score"] == 300


def test_lockouts_clue_values_and_duplicate_scoring(client):
    s = room(client)
    token = s["invites"][0]
    s = command(client, s, "start").json()
    s = command(client, s, "buzz", token=token).json()
    command_id = str(uuid.uuid4())
    old = deepcopy(s)
    s = command(client, s, "judge", {"correct": False}, command_id=command_id).json()
    assert s["players"][0]["score"] == -100
    replay = command(client, old, "judge", {"correct": False}, command_id=command_id)
    assert replay.status_code == 200 and replay.json()["players"][0]["score"] == -100
    assert command(client, old, "judge", {"correct": False}).status_code == 409
    s = command(client, s, "open").json()
    assert command(client, s, "buzz", token=token).status_code == 400
    s = command(client, s, "hint").json()
    assert s["points"] == 200 and not s["locked"]
    s = command(client, s, "open").json()
    s = command(client, s, "buzz", token=token).json()
    s = command(client, s, "judge", {"correct": True}).json()
    assert s["players"][0]["score"] == 100


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


def test_websocket_roles_and_reconnect(client):
    s = room(client)
    path = f"/api/rooms/{s['room_id']}/live"
    with client.websocket_connect(path) as host:
        host.send_json({})
        assert "invites" in host.receive_json()
        with client.websocket_connect(path) as audience:
            audience.send_json({"view": "audience"})
            public = audience.receive_json()
            assert public["you"] == "audience" and "invites" not in public
            host.receive_json()  # Presence update.
            s = command(client, s, "start").json()
            assert host.receive_json()["answer"] == "Ahri"
            assert "answer" not in audience.receive_json()
    with client.websocket_connect(path) as player:
        player.send_json({"token": s["invites"][1]})
        state = player.receive_json()
        assert state["you"] == "1" and "1" in state["online"]
        assert state["index"] == 0 and "answer" not in state
        player.send_text("ping")
        assert player.receive_json() == {"type": "pong"}


def test_cross_origin_mutations_blocked(client):
    assert (
        client.post(
            "/api/rooms",
            headers={"Origin": "https://evil.example"},
            json={"names": ["One", "Two", "Three"]},
        ).status_code
        == 403
    )


def test_timer_pause_and_timeout():
    s = engine.new_game(["A", "B", "C"], QUESTIONS)
    engine.apply(s, "start", "host", {}, now=100)
    engine.apply(s, "buzz", "0", {}, now=100)
    engine.apply(s, "pause", "host", {}, now=105)
    assert s["remaining"] == 10 and not engine.expire(s, now=200)
    engine.apply(s, "resume", "host", {}, now=200)
    assert s["deadline"] == 210
    assert not engine.expire(s, now=209)
    assert engine.expire(s, now=210)
    assert s["players"][0]["score"] == -100 and s["locked"] == ["0"]
    assert not engine.expire(s, now=220)  # Exactly one penalty.


def test_expired_answer_cannot_be_judged_or_submitted(client):
    s = room(client)
    s = command(client, s, "start").json()
    s = command(client, s, "buzz", token=s["invites"][0]).json()
    # Force the persisted server deadline into the past without sleeping.
    server_room = client.app.state.rooms[s["room_id"]]
    server_room["game"]["deadline"] = time.time() - 1
    assert command(client, s, "judge", {"correct": True}).status_code == 409
    updated = get_host(client, s)
    assert updated["players"][0]["score"] == -100
    assert command(client, updated, "judge", {"correct": True}).status_code == 400


def test_non_ascii_password_and_invalid_websocket_token(tmp_path):
    password = "a-private-password-秘密"
    with TestClient(create_app(tmp_path / "unicode.sqlite3", password, QUESTIONS)) as client:
        assert client.post("/api/login", json={"password": password}).status_code == 200
        s = room(client)
        with client.websocket_connect(f"/api/rooms/{s['room_id']}/live") as ws:
            ws.send_json({"token": "invalid-秘密"})
            from starlette.websockets import WebSocketDisconnect

            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()


def test_invalid_question_pack_fails_at_startup(tmp_path):
    invalid = [{"answer": "Ahri", "hints": ["One", "Two"], "points": [300]}]
    with (
        pytest.raises(RuntimeError, match="matching point value"),
        TestClient(create_app(tmp_path / "bad.sqlite3", PASSWORD, invalid)),
    ):
        pass


def test_every_champion_starts_with_open_buzzers(client):
    s = room(client)
    s = command(client, s, "start").json()
    assert s["phase"] == "open"
    s = command(client, s, "reveal").json()
    s = command(client, s, "next").json()
    assert s["phase"] == "open" and s["index"] == 1
