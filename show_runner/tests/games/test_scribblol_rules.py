from copy import deepcopy

import pytest
from app.games.scribblol import rules
from app.games.who_am_i.rules import RuleError

PROMPTS = [{"answer": "Private ability", "hints": ["Draw"], "points": [200]} for _ in range(6)]


def start():
    s = rules.new_game(["Artist", "One", "Two"], PROMPTS)
    rules.apply(s, "start", "host", {}, now=0)
    return s


def test_private_prompt_and_artist_cannot_buzz():
    s = start()
    assert rules.view(s, "0")["answer"] == "Private ability"
    assert rules.view(s, "host")["answer"] == "Private ability"
    for actor in ["1", "2", "audience"]:
        assert "Private ability" not in str(rules.view(s, actor))
    with pytest.raises(RuleError, match="artist cannot buzz"):
        rules.apply(s, "buzz", "0", {}, now=1)


def test_shared_reward_and_queue_clearing():
    s = start()
    rules.apply(s, "buzz", "1", {}, now=10)
    assert s["round_remaining"] == 80 and s["round_deadline"] is None
    rules.apply(s, "buzz", "2", {}, now=11)
    rules.apply(s, "judge", "host", {"correct": False}, now=12)
    assert s["active"] == "2" and s["players"][1]["score"] == 0
    rules.apply(s, "judge", "host", {"correct": True}, now=13)
    assert [p["score"] for p in s["players"]] == [200, 0, 200]
    assert s["queue"] == [] and s["phase"] == "revealed"
    with pytest.raises(RuleError):
        rules.apply(s, "judge", "host", {"correct": True}, now=14)
    assert not rules.expire(s, now=1000)


@pytest.mark.parametrize("ending", ["clock", "skip", "both_wrong", "both_timeout"])
def test_artist_loses_once_when_unsolved(ending):
    s = start()
    if ending == "clock":
        assert rules.expire(s, now=90)
    elif ending == "skip":
        rules.apply(s, "reveal", "host", {}, now=5)
    else:
        rules.apply(s, "buzz", "1", {}, now=1)
        rules.apply(s, "buzz", "2", {}, now=2)
        if ending == "both_timeout":
            assert rules.expire(s, now=16)
            assert rules.expire(s, now=31)
        else:
            rules.apply(s, "judge", "host", {"correct": False}, now=3)
            rules.apply(s, "judge", "host", {"correct": False}, now=4)
    assert [p["score"] for p in s["players"]] == [-100, 0, 0]
    assert s["phase"] == "revealed" and s["active"] is None
    assert not rules.expire(s, now=1000)
    with pytest.raises(RuleError):
        rules.apply(s, "reveal", "host", {}, now=1000)


def test_drawing_clock_pause_guess_resume_and_rotation():
    s = start()
    rules.apply(s, "pause", "host", {}, now=10)
    assert not rules.expire(s, now=200)
    rules.apply(s, "resume", "host", {}, now=200)
    assert s["round_deadline"] == 280
    rules.apply(s, "buzz", "1", {}, now=210)
    rules.apply(s, "submit_answer", "1", {"answer": "x"}, now=211)
    assert not rules.expire(s, now=300)
    rules.apply(s, "judge", "host", {"correct": False}, now=310)
    assert s["round_deadline"] == 380
    for index in range(6):
        assert s["artist"] == str(index % 3)
        rules.apply(s, "reveal", "host", {}, now=320)
        rules.apply(s, "next", "host", {}, now=321)
    assert s["phase"] == "finished"
    assert [p["score"] for p in s["players"]] == [-200, -200, -200]


def test_strokes_are_bounded_authorized_and_reset():
    s = start()
    stroke = {"question_index": 0, "color": "#172d39", "width": 6, "points": [[0, 0], [1, 1]]}
    with pytest.raises(RuleError):
        rules.apply(s, "draw", "1", stroke, now=1)
    for bad in [
        {**stroke, "points": [[float("nan"), 0]]},
        {**stroke, "points": [[2, 0]]},
        {**stroke, "points": [[0, 0]] * 129},
        {**stroke, "question_index": 1},
    ]:
        with pytest.raises(RuleError):
            rules.apply(s, "draw", "0", bad, now=1)
    rules.apply(s, "draw", "0", stroke, now=1)
    assert len(rules.view(s, "audience")["strokes"]) == 1
    rules.apply(s, "erase_stroke", "0", {"question_index": 0}, now=2)
    assert s["strokes"] == []
    rules.apply(s, "draw", "0", stroke, now=3)
    rules.apply(s, "clear_canvas", "0", {"question_index": 0}, now=4)
    assert s["strokes"] == []
    rules.apply(s, "draw", "0", stroke, now=5)
    rules.apply(s, "buzz", "1", {}, now=6)
    before = deepcopy(s)
    with pytest.raises(RuleError):
        rules.apply(s, "draw", "0", stroke, now=7)
    assert s == before
    rules.apply(s, "judge", "host", {"correct": True}, now=8)
    rules.apply(s, "next", "host", {}, now=9)
    assert s["strokes"] == [] and s["artist"] == "1"
