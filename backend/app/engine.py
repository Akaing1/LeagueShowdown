"""Pure game rules. Every state transition is serialized and persisted by the server."""

import time
from copy import deepcopy


class RuleError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RuleError(message)


def new_game(names, questions):
    return {
        "players": [{"id": str(i), "name": name, "score": 0} for i, name in enumerate(names)],
        "questions": deepcopy(questions),
        "index": -1,
        "revealed": 0,
        "phase": "lobby",
        "active": None,
        "locked": [],
        "submission": None,
        "deadline": None,
        "paused": False,
        "remaining": None,
        "answer_seconds": 15,
        "wrong_penalty": 100,
        "last_result": None,
    }


def question(state):
    return state["questions"][state["index"]] if state["index"] >= 0 else None


def current_points(state):
    q = question(state)
    return q["points"][max(0, state["revealed"] - 1)] if q else 0


def wrong(state, reason):
    player = next(p for p in state["players"] if p["id"] == state["active"])
    player["score"] -= state["wrong_penalty"]
    state["last_result"] = {
        "player": player["name"],
        "correct": False,
        "points": -state["wrong_penalty"],
        "reason": reason,
    }
    state["locked"].append(state["active"])
    state.update(active=None, submission=None, deadline=None, phase="clue")


def expire(state, now=None):
    now = time.time() if now is None else now
    if (
        not state["paused"]
        and state["phase"] == "answering"
        and state["deadline"] is not None
        and now >= state["deadline"]
    ):
        wrong(state, "Time expired")
        return True
    return False


def apply(state, action, actor, payload, now=None):
    now = time.time() if now is None else now
    host = actor == "host"
    require(host or action in {"buzz", "submit_answer"}, "Host access required")
    require(not state["paused"] or action == "resume", "The show is paused")
    if action in {"start", "next"}:
        require(state["phase"] in {"lobby", "revealed"}, "Reveal the current answer first")
        require(len(state["players"]) == 3, "Exactly three contestants are required")
        index = state["index"] + 1
        if index >= len(state["questions"]):
            state["phase"] = "finished"
            return
        state.update(
            index=index,
            revealed=1,
            phase="clue",
            active=None,
            locked=[],
            submission=None,
            deadline=None,
            last_result=None,
        )
    elif action == "hint":
        q = question(state)
        require(state["phase"] in {"clue", "open"}, "Cannot reveal a clue now")
        require(state["revealed"] < len(q["hints"]), "All clues are already visible")
        state["revealed"] += 1
        # A new clue gives everyone another attempt; a wrong guess stays locked until then.
        state.update(phase="clue", locked=[])
    elif action == "open":
        require(state["phase"] == "clue", "Buzzers cannot open now")
        require(len(state["locked"]) < 3, "Reveal another clue or the answer")
        state["phase"] = "open"
    elif action == "buzz":
        require(not host and actor in [p["id"] for p in state["players"]], "Contestant required")
        require(state["phase"] == "open", "Buzzers are closed")
        require(actor not in state["locked"], "Wait for the next clue")
        state.update(
            phase="answering", active=actor, deadline=now + state["answer_seconds"], submission=None
        )
    elif action == "submit_answer":
        require(
            state["phase"] == "answering" and state["active"] == actor,
            "It is not your turn to answer",
        )
        text = payload.get("answer")
        require(
            isinstance(text, str) and 0 < len(text.strip()) <= 120,
            "Answer must contain 1–120 characters",
        )
        state.update(submission=text.strip(), phase="judging", deadline=None)
    elif action == "judge":
        require(state["phase"] in {"answering", "judging"}, "No answer to judge")
        correct = payload.get("correct")
        require(type(correct) is bool, "Choose correct or incorrect")
        if correct:
            player = next(p for p in state["players"] if p["id"] == state["active"])
            points = current_points(state)
            player["score"] += points
            state["last_result"] = {
                "player": player["name"],
                "correct": True,
                "points": points,
                "reason": "Correct answer",
            }
            state.update(phase="revealed", active=None, submission=None, deadline=None)
        else:
            wrong(state, "Incorrect answer")
    elif action == "reveal":
        require(state["phase"] in {"clue", "open"}, "Judge the active contestant first")
        state.update(phase="revealed", deadline=None)
    elif action == "pause":
        require(state["phase"] not in {"lobby", "finished"}, "No active round")
        state["remaining"] = max(0, state["deadline"] - now) if state["deadline"] else None
        state.update(paused=True, deadline=None)
    elif action == "resume":
        require(state["paused"], "The show is not paused")
        state["deadline"] = now + state["remaining"] if state["remaining"] is not None else None
        state.update(paused=False, remaining=None)
    elif action == "adjust":
        player = next((p for p in state["players"] if p["id"] == payload.get("player")), None)
        points = payload.get("points")
        require(
            player is not None and type(points) is int and abs(points) <= 10000,
            "Choose a contestant and a whole-number adjustment up to 10,000 points",
        )
        player["score"] += points
    else:
        raise RuleError("Unknown action")


def view(state, actor):
    q = question(state)
    result = {
        key: deepcopy(state[key])
        for key in (
            "players",
            "index",
            "revealed",
            "phase",
            "active",
            "locked",
            "deadline",
            "paused",
            "remaining",
            "answer_seconds",
            "wrong_penalty",
            "last_result",
        )
    }
    result.update(
        total=len(state["questions"]),
        hints=q["hints"][: state["revealed"]] if q else [],
        points=current_points(state),
        hint_count=len(q["hints"]) if q else 0,
    )
    if actor == "host":
        result.update(
            answer=q["answer"] if q else None,
            all_hints=q["hints"] if q else [],
            submission=state["submission"],
        )
    elif state["phase"] in {"revealed", "finished"}:
        result["answer"] = q["answer"] if q else None
    if actor == state["active"]:
        result["submission"] = state["submission"]
    return result
