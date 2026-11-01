import uuid

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
