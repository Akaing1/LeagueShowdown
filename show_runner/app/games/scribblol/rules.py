"""Drawing rounds with private ability prompts and shared, bounded vector strokes."""

import math
import time
from copy import deepcopy

from ..who_am_i import rules as quiz

require = quiz.require
COLORS = {"#172d39", "#e74c3c", "#2e86de", "#27ae60", "#f1c40f", "#ffffff"}
DRAW_ACTIONS = {"draw", "erase_stroke", "clear_canvas"}


def new_game(names, prompts):
    state = quiz.new_game(names, prompts)
    state.update(
        game_type="scribblol",
        artist=None,
        strokes=[],
        round_seconds=90,
        round_deadline=None,
        round_remaining=90,
        wrong_penalty=0,
    )
    return state


def finish_unsolved(state, reason):
    artist = next(p for p in state["players"] if p["id"] == state["artist"])
    artist["score"] -= 100
    state.update(
        phase="revealed",
        active=None,
        queue=[],
        deadline=None,
        submission=None,
        round_deadline=None,
        last_result={"player": artist["name"], "correct": False, "points": -100, "reason": reason},
    )


def resume_drawing(state, now):
    if state["phase"] == "open":
        if len(state["locked"]) >= 2:
            finish_unsolved(state, "Nobody guessed correctly · artist −100")
        else:
            state["round_deadline"] = now + state["round_remaining"]


def expire(state, now=None):
    now = time.time() if now is None else now
    if state["paused"]:
        return False
    if quiz.expire(state, now):
        resume_drawing(state, now)
        return True
    if (
        state["phase"] == "open"
        and state["round_deadline"] is not None
        and now >= state["round_deadline"]
    ):
        finish_unsolved(state, "Drawing time expired · artist −100")
        return True
    return False


def apply(state, action, actor, payload, now=None):
    now = time.time() if now is None else now
    require(not state["paused"] or action == "resume", "The show is paused")
    if action in DRAW_ACTIONS:
        require(actor == state["artist"], "Only the artist can draw")
        require(state["phase"] == "open", "Drawing is paused while a guess is answered")
        require(
            type(payload.get("question_index")) is int
            and payload["question_index"] == state["index"],
            "The round changed",
        )
        if action == "clear_canvas":
            state["strokes"] = []
        elif action == "erase_stroke":
            require(bool(state["strokes"]), "Nothing to erase")
            state["strokes"].pop()
        else:
            points = payload.get("points")
            require(len(state["strokes"]) < 200, "Canvas is full; undo or clear to continue")
            require(isinstance(points, list) and 1 <= len(points) <= 128, "Invalid stroke length")
            require(
                isinstance(payload.get("color"), str)
                and payload["color"] in COLORS
                and type(payload.get("width")) is int
                and 3 <= payload["width"] <= 24,
                "Invalid brush",
            )
            require(
                all(
                    isinstance(p, list)
                    and len(p) == 2
                    and all(type(v) in {int, float} and math.isfinite(v) and 0 <= v <= 1 for v in p)
                    for p in points
                ),
                "Invalid stroke coordinates",
            )
            state["strokes"].append(
                {"points": deepcopy(points), "color": payload["color"], "width": payload["width"]}
            )
        return
    require(action not in {"hint", "open"}, "Not a drawing game action")
    if action == "buzz":
        require(actor != state["artist"], "The artist cannot buzz")
        if state["phase"] == "open":
            state["round_remaining"] = max(0, state["round_deadline"] - now)
    if action == "reveal":
        require(actor == "host", "Host access required")
        require(state["phase"] == "open", "Judge the active guess first")
        finish_unsolved(state, "Round ended without a correct guess · artist −100")
        return
    if action == "pause" and state["phase"] == "open":
        state["round_remaining"] = max(0, state["round_deadline"] - now)
    quiz.apply(state, action, actor, payload, now)
    if action in {"start", "next"} and state["phase"] != "finished":
        state.update(
            artist=str(state["index"] % 3), strokes=[], round_remaining=90, round_deadline=now + 90
        )
    elif action == "buzz":
        state["round_deadline"] = None
    elif action == "judge":
        if payload["correct"]:
            artist = next(p for p in state["players"] if p["id"] == state["artist"])
            artist["score"] += 200
            state["last_result"]["reason"] = f"Correct · {artist['name']} also earns +200"
            state["round_deadline"] = None
        else:
            resume_drawing(state, now)
    elif action == "pause":
        state["round_deadline"] = None
    elif action == "resume":
        resume_drawing(state, now)


def view(state, actor):
    result = quiz.view(state, actor)
    result.update(
        game_type="scribblol",
        artist=state["artist"],
        strokes=deepcopy(state["strokes"]),
        round_deadline=state["round_deadline"],
        round_remaining=state["round_remaining"],
    )
    if actor == state["artist"]:
        q = quiz.question(state)
        result["answer"] = q["answer"] if q else None
    return result
