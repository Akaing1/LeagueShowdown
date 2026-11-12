from tests.support import PASSWORD, command


def test_shop_questions_scoring_queue_and_reset(client):
    client.post("/api/login", json={"password": PASSWORD})
    s = client.post(
        "/api/rooms", json={"names": ["A", "B", "C"], "game_type": "shoplifting"}
    ).json()
    assert s["game_type"] == "shoplifting" and s["total"] == 8
    s = command(client, s, "start").json()
    tokens = s["invites"]
    assert s["points"] == 100 and len(s["hints"]) == 1
    original = s
    s = command(client, s, "buzz", {"question_index": 0}, token=tokens[0]).json()
    s = command(client, original, "buzz", {"question_index": 0}, token=tokens[1]).json()
    assert s["queue"] == ["1"]
    s = command(client, s, "judge", {"correct": False}).json()
    assert s["active"] == "1" and s["locked"] == ["0"]
    s = command(client, s, "judge", {"correct": True}).json()
    assert [p["score"] for p in s["players"]] == [-100, 100, 0]
    s = command(client, s, "next").json()
    assert s["phase"] == "open" and s["locked"] == []
