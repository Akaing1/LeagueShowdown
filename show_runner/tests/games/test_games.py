import pytest
from app.config import DEFAULT_QUESTIONS
from app.games.who_am_i import rules as engine
from tests.support import QUESTIONS


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


def test_default_pack_eight_rounds_and_four_hint_scoring():
    import json

    pack = json.loads(DEFAULT_QUESTIONS.read_text())
    assert len(pack) == 8
    for hint_count in range(1, 5):
        state = engine.new_game(["A", "B", "C"], pack)
        for index in range(8):
            engine.apply(state, "start" if index == 0 else "next", "host", {})
            assert len(engine.question(state)["hints"]) == 4
            for _ in range(hint_count - 1):
                engine.apply(state, "hint", "host", {})
            engine.apply(state, "buzz", "0", {})
            engine.apply(state, "judge", "host", {"correct": True})
            expected = (index + 1) * (200 if hint_count == 1 else 100)
            assert state["players"][0]["score"] == expected
        engine.apply(state, "next", "host", {})
        assert state["phase"] == "finished"


@pytest.mark.parametrize("timeout", [False, True])
def test_round_lockouts_reopen_for_others_and_reset_on_next_question(timeout):
    state = engine.new_game(["A", "B", "C"], QUESTIONS)
    engine.apply(state, "start", "host", {})
    for player in range(3):
        engine.apply(state, "buzz", str(player), {}, now=0)
        if timeout:
            assert engine.expire(state, now=16)
        else:
            engine.apply(state, "judge", "host", {"correct": False})
        assert state["locked"] == [str(i) for i in range(player + 1)]
        assert state["phase"] == ("open" if player < 2 else "clue")
        if player < 2:
            engine.apply(state, "hint", "host", {})
        with pytest.raises(engine.RuleError):
            engine.apply(state, "buzz", str(player), {})
    with pytest.raises(engine.RuleError):
        engine.apply(state, "open", "host", {})
    engine.apply(state, "reveal", "host", {})
    engine.apply(state, "next", "host", {})
    assert state["locked"] == [] and state["phase"] == "open"
    engine.apply(state, "buzz", "0", {})


@pytest.mark.parametrize("timeout", [False, True])
def test_buzzer_queue_promotes_in_order_with_fresh_timer(timeout):
    s = engine.new_game(["A", "B", "C"], QUESTIONS)
    engine.apply(s, "start", "host", {}, now=0)
    engine.apply(s, "buzz", "0", {}, now=1)
    engine.apply(s, "buzz", "2", {}, now=2)
    engine.apply(s, "buzz", "1", {}, now=3)
    assert s["active"] == "0" and s["queue"] == ["2", "1"] and s["deadline"] == 16
    for actor in ["0", "1", "2"]:
        with pytest.raises(engine.RuleError, match="Already buzzed"):
            engine.apply(s, "buzz", actor, {}, now=4)
    if timeout:
        assert engine.expire(s, now=20)
    else:
        engine.apply(s, "submit_answer", "0", {"answer": "Wrong"}, now=4)
        engine.apply(s, "judge", "host", {"correct": False}, now=20)
    assert s["active"] == "2" and s["queue"] == ["1"] and s["deadline"] == 35
    assert s["submission"] is None and s["locked"] == ["0"]
    engine.apply(s, "judge", "host", {"correct": False}, now=21)
    assert s["active"] == "1" and s["queue"] == [] and s["deadline"] == 36
    engine.apply(s, "judge", "host", {"correct": False}, now=22)
    assert s["active"] is None and s["phase"] == "clue"
    engine.apply(s, "reveal", "host", {})
    engine.apply(s, "next", "host", {})
    assert s["locked"] == [] and s["queue"] == []


def test_queue_during_judging_pause_correct_and_old_rooms():
    s = engine.new_game(["A", "B", "C"], QUESTIONS)
    del s["queue"]  # Rooms saved before queues were introduced.
    assert engine.view(s, "audience")["queue"] == []
    engine.apply(s, "start", "host", {})
    engine.apply(s, "buzz", "0", {}, now=0)
    engine.apply(s, "submit_answer", "0", {"answer": "Ahri"})
    engine.apply(s, "buzz", "1", {})
    engine.apply(s, "pause", "host", {})
    with pytest.raises(engine.RuleError, match="paused"):
        engine.apply(s, "buzz", "2", {})
    assert not engine.expire(s, now=100)
    assert s["queue"] == ["1"]
    engine.apply(s, "resume", "host", {})
    engine.apply(s, "judge", "host", {"correct": True})
    assert s["queue"] == [] and s["phase"] == "revealed"
    assert s["players"][1]["score"] == 0
    with pytest.raises(engine.RuleError, match="closed"):
        engine.apply(s, "buzz", "2", {})
