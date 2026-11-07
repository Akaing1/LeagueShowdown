import pytest
from app.games.splash_zone import rules
from app.games.who_am_i.rules import RuleError

CHAMPIONS = [{"answer": f"Champion {i}", "asset": f"Champion{i}"} for i in range(12)]


def start():
    state = rules.new_game(["A", "B", "C"], CHAMPIONS)
    rules.apply(state, "start", "host", {}, now=0)
    return state


def test_random_rounds_crop_and_private_answer():
    s = start()
    assert len(s["questions"]) == 8
    assert len({q["answer"] for q in s["questions"]}) == 8
    assert all(0 <= v <= 1 for q in s["questions"] for v in q["crop"])
    public = rules.view(s, "audience")
    assert "answer" not in public and "all_hints" not in public
    assert public["splash_url"].endswith("_0.jpg")
    assert public["round_deadline"] == 30
    assert rules.view(s, "host")["answer"] == s["questions"][0]["answer"]


def test_zoom_frozen_through_queue_and_judging_then_resumes():
    s = start()
    rules.apply(s, "buzz", "0", {}, now=10)
    rules.apply(s, "buzz", "1", {}, now=11)
    rules.apply(s, "buzz", "2", {}, now=12)
    assert s["queue"] == ["1", "2"]
    assert s["round_remaining"] == 20 and s["round_deadline"] is None
    rules.apply(s, "submit_answer", "0", {"answer": "guess"}, now=13)
    assert not rules.expire(s, now=100)
    rules.apply(s, "judge", "host", {"correct": False}, now=100)
    assert s["active"] == "1" and s["round_deadline"] is None
    assert rules.expire(s, now=115)
    assert s["active"] == "2" and s["round_remaining"] == 20
    rules.apply(s, "judge", "host", {"correct": True}, now=116)
    assert [p["score"] for p in s["players"]] == [-100, -100, 200]
    assert s["phase"] == "revealed" and s["queue"] == []
    assert not rules.expire(s, now=1000)
    rules.apply(s, "next", "host", {}, now=200)
    assert s["locked"] == [] and s["round_deadline"] == 230


def test_wrong_answer_resume_and_host_pause_preserve_budget():
    s = start()
    rules.apply(s, "buzz", "0", {}, now=5)
    rules.apply(s, "judge", "host", {"correct": False}, now=20)
    assert s["round_deadline"] == 45
    rules.apply(s, "pause", "host", {}, now=25)
    assert s["round_remaining"] == 20
    assert not rules.expire(s, now=100)
    rules.apply(s, "resume", "host", {}, now=100)
    assert s["round_deadline"] == 120
    rules.apply(s, "buzz", "1", {}, now=105)
    rules.apply(s, "pause", "host", {}, now=106)
    rules.apply(s, "resume", "host", {}, now=200)
    assert s["deadline"] == 214 and s["round_deadline"] is None
    assert rules.expire(s, now=214)
    assert s["round_deadline"] == 229


def test_full_splash_stays_guessable_and_all_wrong_closes_round():
    s = start()
    assert rules.expire(s, now=30)
    assert not rules.expire(s, now=31)
    assert s["phase"] == "open" and s["round_remaining"] == 0
    for seat in ["0", "1", "2"]:
        rules.apply(s, "buzz", seat, {}, now=40)
        rules.apply(s, "judge", "host", {"correct": False}, now=41)
        with pytest.raises(RuleError):
            rules.apply(s, "buzz", seat, {}, now=42)
    assert s["phase"] == "clue"
    rules.apply(s, "reveal", "host", {}, now=43)
    assert rules.view(s, "audience")["answer"] == s["questions"][0]["answer"]


def test_invalid_actions_do_not_change_clock():
    s = start()
    for action, actor in [
        ("hint", "host"),
        ("open", "host"),
        ("buzz", "host"),
        ("buzz", "audience"),
    ]:
        with pytest.raises(RuleError):
            rules.apply(s, action, actor, {}, now=4)
        assert s["round_deadline"] == 30
