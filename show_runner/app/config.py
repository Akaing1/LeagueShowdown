import json
import os
from pathlib import Path

from .models.requests import Question

APP_ROOT = Path(__file__).resolve().parent
DEFAULT_QUESTIONS = APP_ROOT / "content" / "who_am_i" / "default.json"
STAGE_DIST = APP_ROOT.parents[1] / "show_stage" / "dist"


def host_password(override=None):
    password = override or os.getenv("SHOWDOWN_HOST_PASSWORD", "")
    if len(password) < 16:
        raise RuntimeError(
            "Set SHOWDOWN_HOST_PASSWORD to a private password of at least 16 characters"
        )
    return password


def database_path(override=None):
    return override or os.getenv("SHOWDOWN_DB", "data/showdown.sqlite3")


def secure_cookie():
    return os.getenv("SHOWDOWN_SECURE_COOKIE") == "1"


def load_questions(source=None):
    if source is None:
        source = json.loads(Path(os.getenv("SHOWDOWN_QUESTIONS", DEFAULT_QUESTIONS)).read_text())
    if not isinstance(source, list) or not 1 <= len(source) <= 100:
        raise RuntimeError("Question pack must contain 1–100 questions")
    questions = [Question.model_validate(q).model_dump() for q in source]
    if any(len(q["hints"]) != len(q["points"]) for q in questions):
        raise RuntimeError("Each clue must have a matching point value")
    return questions


def valid_origin(origin, host):
    allowed = {f"http://{host}", f"https://{host}"}
    allowed.update(
        os.getenv("SHOWDOWN_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(
            ","
        )
    )
    return origin is None or origin in allowed
