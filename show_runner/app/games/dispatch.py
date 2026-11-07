"""Game selection, with backward compatibility for saved Who Am I rooms."""

from .scribblol import rules as drawing
from .splash_zone import rules as splash
from .who_am_i import rules as quiz

RuleError = quiz.RuleError
require = quiz.require


def rules(state):
    return {"scribblol": drawing, "splash_zone": splash}.get(state.get("game_type"), quiz)


def new_game(names, questions, game_type="who_am_i"):
    return rules({"game_type": game_type}).new_game(names, questions)


def apply(state, action, actor, payload, now=None):
    return rules(state).apply(state, action, actor, payload, now)


def expire(state, now=None):
    return rules(state).expire(state, now)


def view(state, actor):
    result = rules(state).view(state, actor)
    result.setdefault("game_type", "who_am_i")
    return result
