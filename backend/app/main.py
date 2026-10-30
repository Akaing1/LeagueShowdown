import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
from contextlib import asynccontextmanager, suppress
from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from . import engine
from .store import Store


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=120)
    hints: list[str] = Field(min_length=1, max_length=6)
    points: list[int] = Field(min_length=1, max_length=6)

    @field_validator("hints")
    @classmethod
    def hints_valid(cls, hints):
        if any(not h.strip() or len(h) > 500 for h in hints):
            raise ValueError("Clues must contain 1–500 characters")
        return hints

    @field_validator("points")
    @classmethod
    def points_valid(cls, points):
        if any(p < 0 or p > 10000 for p in points):
            raise ValueError("Points must be between 0 and 10,000")
        return points


class CreateRoom(BaseModel):
    names: list[str] = Field(min_length=3, max_length=3)

    @field_validator("names")
    @classmethod
    def names_valid(cls, names):
        names = [name.strip() for name in names]
        if any(not name or len(name) > 32 for name in names):
            raise ValueError("Names must contain 1–32 characters")
        if len({name.casefold() for name in names}) != 3:
            raise ValueError("Use three different contestant names")
        return names


class Login(BaseModel):
    password: str = Field(max_length=256)


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=8, max_length=80)
    revision: int = Field(ge=0)
    action: str = Field(max_length=32)
    payload: dict = Field(default_factory=dict)


def create_app(db_path=None, password=None, questions=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.password = password or os.getenv("SHOWDOWN_HOST_PASSWORD", "")
        if len(app.state.password) < 16:
            raise RuntimeError(
                "Set SHOWDOWN_HOST_PASSWORD to a private password of at least 16 characters"
            )
        source = questions
        if source is None:
            path = Path(os.getenv("SHOWDOWN_QUESTIONS", Path(__file__).with_name("questions.json")))
            source = json.loads(path.read_text())
        if not isinstance(source, list) or not 1 <= len(source) <= 100:
            raise RuntimeError("Question pack must contain 1–100 questions")
        app.state.questions = [Question.model_validate(q).model_dump() for q in source]
        if any(len(q["hints"]) != len(q["points"]) for q in app.state.questions):
            raise RuntimeError("Each clue must have a matching point value")
        app.state.store = Store(db_path or os.getenv("SHOWDOWN_DB", "data/showdown.sqlite3"))
        app.state.rooms = app.state.store.all()
        app.state.lock = asyncio.Lock()
        app.state.clients = {}
        app.state.attempts = {}
        task = asyncio.create_task(tick())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            for clients in list(app.state.clients.values()):
                for ws in list(clients):
                    with suppress(Exception):
                        await ws.close(code=1001)
            app.state.store.close()

    app = FastAPI(title="League Showdown", version="0.1.0", lifespan=lifespan)

    def valid_origin(origin, host):
        allowed = {f"http://{host}", f"https://{host}"}
        allowed.update(
            os.getenv(
                "SHOWDOWN_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
        )
        return origin is None or origin in allowed

    @app.middleware("http")
    async def browser_security(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"} and not valid_origin(
            request.headers.get("origin"), request.headers.get("host")
        ):
            return Response("Origin not allowed", status_code=403)
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def signature(value):
        return hmac.new(app.state.password.encode(), value.encode(), hashlib.sha256).hexdigest()

    def host_authenticated(cookies):
        token = cookies.get("showdown_host", "")
        try:
            expiry, sig = token.split(".", 1)
            return int(expiry) > time.time() and hmac.compare_digest(sig, signature(expiry))
        except (ValueError, TypeError):
            return False

    def room_or_404(room_id):
        room = app.state.rooms.get(room_id)
        if room is None:
            raise HTTPException(404, "Show not found")
        return room

    def actor_for(room, token, cookies):
        # Explicit contestant credentials take priority when testing seats in the host browser.
        if token:
            for index, invite in enumerate(room["invites"]):
                if secrets.compare_digest(invite.encode(), token.encode()):
                    return str(index)
            raise HTTPException(403, "Invalid contestant link")
        if host_authenticated(cookies):
            return "host"
        return "audience"

    def snapshot(room, actor):
        state = engine.view(room["game"], actor)
        state.update(
            room_id=room["id"],
            revision=room["revision"],
            you=actor,
            server_time=time.time(),
            online=[
                p for p in ["0", "1", "2"] if p in app.state.clients.get(room["id"], {}).values()
            ],
        )
        if actor == "host":
            state.update(invites=room["invites"], can_undo=bool(room["history"]))
        return state

    async def send(ws, state):
        try:
            await asyncio.wait_for(ws.send_json(state), timeout=2)
        except (WebSocketDisconnect, TimeoutError, RuntimeError, OSError):
            for clients in app.state.clients.values():
                clients.pop(ws, None)
            with suppress(Exception):
                await ws.close(code=1011)

    async def broadcast(room):
        clients = list(app.state.clients.get(room["id"], {}).items())
        await asyncio.gather(*(send(ws, snapshot(room, actor)) for ws, actor in clients))

    def commit(previous, game, command_id=None, undo=False):
        room = deepcopy(previous)
        if undo:
            room["history"].pop()
        else:
            room["history"] = (room["history"] + [previous["game"]])[-30:]
        room["game"] = game
        room["revision"] += 1
        if command_id:
            room["commands"] = (room["commands"] + [command_id])[-256:]
        # Publish in memory only after the transaction has succeeded.
        app.state.store.save(room)
        app.state.rooms[room["id"]] = room
        return room

    async def tick():
        while True:
            await asyncio.sleep(0.25)
            async with app.state.lock:
                for room in list(app.state.rooms.values()):
                    game = deepcopy(room["game"])
                    if engine.expire(game):
                        updated = commit(room, game)
                        await broadcast(updated)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/api/login")
    async def login(body: Login, request: Request, response: Response):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        app.state.attempts = {k: v for k, v in app.state.attempts.items() if v[0] > now - 60}
        first, count = app.state.attempts.get(ip, (now, 0))
        if count >= 10:
            raise HTTPException(429, "Too many attempts. Try again in a minute.")
        if not secrets.compare_digest(body.password.encode(), app.state.password.encode()):
            app.state.attempts[ip] = (first, count + 1)
            raise HTTPException(401, "Incorrect host password")
        app.state.attempts.pop(ip, None)
        expiry = str(int(now + 43200))
        response.set_cookie(
            "showdown_host",
            f"{expiry}.{signature(expiry)}",
            httponly=True,
            samesite="strict",
            max_age=43200,
            secure=os.getenv("SHOWDOWN_SECURE_COOKIE") == "1",
        )
        return {"ok": True}

    @app.post("/api/logout")
    async def logout(response: Response):
        response.delete_cookie("showdown_host")
        return {"ok": True}

    @app.get("/api/rooms")
    async def list_rooms(request: Request):
        if not host_authenticated(request.cookies):
            raise HTTPException(401, "Sign in as host")
        return [
            {
                "id": r["id"],
                "names": [p["name"] for p in r["game"]["players"]],
                "phase": r["game"]["phase"],
            }
            for r in reversed(list(app.state.rooms.values()))
        ]

    @app.post("/api/rooms", status_code=201)
    async def create_room(body: CreateRoom, request: Request):
        if not host_authenticated(request.cookies):
            raise HTTPException(401, "Sign in as host")
        async with app.state.lock:
            room = {
                "id": secrets.token_urlsafe(12),
                "revision": 0,
                "invites": [secrets.token_urlsafe(32) for _ in range(3)],
                "game": engine.new_game(body.names, app.state.questions),
                "history": [],
                "commands": [],
            }
            app.state.store.save(room)
            app.state.rooms[room["id"]] = room
            return snapshot(room, "host")

    @app.get("/api/rooms/{room_id}")
    async def get_room(room_id: str, request: Request):
        room = room_or_404(room_id)
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        actor = (
            "audience"
            if request.headers.get("x-showdown-view") == "audience"
            else actor_for(room, token, request.cookies)
        )
        return snapshot(room, actor)

    @app.post("/api/rooms/{room_id}/commands")
    async def command(room_id: str, body: Command, request: Request):
        async with app.state.lock:
            room = room_or_404(room_id)
            token = request.headers.get("authorization", "").removeprefix("Bearer ")
            actor = actor_for(room, token, request.cookies)
            if actor == "audience":
                raise HTTPException(403, "Contestant or host access required")
            # Deduplication is scoped to the actor, and checked before revision validation.
            command_id = f"{actor}:{body.id}"
            if command_id in room["commands"]:
                return snapshot(room, actor)
            game = deepcopy(room["game"])
            if engine.expire(game):
                room = commit(room, game)
                await broadcast(room)
            if body.revision != room["revision"]:
                raise HTTPException(409, "The show changed. Please try again.")
            game = deepcopy(room["game"])
            undo = body.action == "undo"
            try:
                if undo:
                    engine.require(actor == "host", "Host access required")
                    engine.require(bool(room["history"]), "Nothing to undo")
                    game = deepcopy(room["history"][-1])
                    if game["phase"] not in {"lobby", "finished"}:
                        game.update(
                            paused=True,
                            deadline=None,
                            remaining=game["answer_seconds"]
                            if game["phase"] == "answering"
                            else None,
                        )
                else:
                    engine.apply(game, body.action, actor, body.payload)
            except engine.RuleError as error:
                raise HTTPException(400, str(error)) from error
            room = commit(room, game, command_id, undo=undo)
            await broadcast(room)
            return snapshot(room, actor)

    @app.websocket("/api/rooms/{room_id}/live")
    async def live(ws: WebSocket, room_id: str):
        if not valid_origin(ws.headers.get("origin"), ws.headers.get("host")):
            await ws.close(code=1008)
            return
        await ws.accept()
        registered = False
        try:
            auth = await asyncio.wait_for(ws.receive_json(), timeout=5)
            if not isinstance(auth, dict) or not isinstance(auth.get("token", ""), str):
                await ws.close(code=1008)
                return
            async with app.state.lock:
                room = room_or_404(room_id)
                actor = (
                    "audience"
                    if auth.get("view") == "audience"
                    else actor_for(room, auth.get("token", ""), ws.cookies)
                )
                clients = app.state.clients.setdefault(room_id, {})
                if len(clients) >= 24:
                    await ws.close(code=1013)
                    return
                clients[ws] = actor
                registered = True
                await broadcast(room)
            while True:
                message = await ws.receive_text()
                if message == "ping":
                    await ws.send_json({"type": "pong"})
        except (TimeoutError, WebSocketDisconnect, HTTPException, ValueError, ValidationError):
            with suppress(Exception):
                await ws.close(code=1008)
        finally:
            if registered:
                async with app.state.lock:
                    app.state.clients.get(room_id, {}).pop(ws, None)
                    await broadcast(app.state.rooms[room_id])

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}")
        async def frontend(path: str):
            if path.startswith("api/"):
                raise HTTPException(404, "Not found")
            return FileResponse(dist / "index.html")

    return app


app = create_app()
