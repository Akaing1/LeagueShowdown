"""Random splash crops with a shared, pausable 30-second reveal clock."""

import secrets
import time

from ..who_am_i import rules as quiz

require = quiz.require


def new_game(names, champions):
    selected = secrets.SystemRandom().sample(champions, min(8, len(champions)))
    questions = [
        {
            **champion,
            "hints": ["Name the champion from their splash art."],
            "points": [200],
            "crop": [secrets.randbelow(10001) / 10000 for _ in range(2)],
        }
        for champion in selected
    ]
    state = quiz.new_game(names, questions)
    state.update(game_type="splash_zone", round_deadline=None, round_remaining=30)
    return state


def resume_zoom(state, now):
    if state["phase"] == "open" and state["round_remaining"] > 0:
        state["round_deadline"] = now + state["round_remaining"]


def freeze_zoom(state, now):
    if state["round_deadline"] is not None:
        state["round_remaining"] = max(0, state["round_deadline"] - now)
    state["round_deadline"] = None


def expire(state, now=None):
    now = time.time() if now is None else now
    if state["paused"]:
        return False
    if quiz.expire(state, now):
        resume_zoom(state, now)
        return True
    if state["round_deadline"] is not None and now >= state["round_deadline"]:
        state.update(round_remaining=0, round_deadline=None)
        return True
    return False


def apply(state, action, actor, payload, now=None):
    now = time.time() if now is None else now
    require(action not in {"hint", "open"}, "Not a Splash Zone action")
    # Validate before modifying clocks, including duplicate or unauthorized buzzes.
    old_phase = state["phase"]
    old_deadline = state["round_deadline"]
    quiz.apply(state, action, actor, payload, now)
    if action in {"start", "next"} and state["phase"] != "finished":
        state.update(round_remaining=30, round_deadline=now + 30)
    elif action == "pause" or (action == "buzz" and old_phase == "open"):
        state["round_deadline"] = old_deadline
        freeze_zoom(state, now)
    elif action == "resume" or (action == "judge" and not payload["correct"]):
        resume_zoom(state, now)
    if state["phase"] in {"revealed", "clue", "finished"}:
        freeze_zoom(state, now)


def view(state, actor):
    result = quiz.view(state, actor)
    q = quiz.question(state)
    result.update(
        game_type="splash_zone",
        round_deadline=state["round_deadline"],
        round_remaining=state["round_remaining"],
        splash_url=(
            f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{q['asset']}_0.jpg"
            if q
            else None
        ),
        crop=q["crop"] if q else [0.5, 0.5],
    )
    return result
