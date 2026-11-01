import secrets

from fastapi import HTTPException, Request

from ..games.who_am_i import rules as engine
from ..models.requests import Command, CreateRoom


def register(app, auth, rooms):
    @app.get("/api/rooms")
    async def list_rooms(request: Request):
        if not auth.host_authenticated(request.cookies):
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
        if not auth.host_authenticated(request.cookies):
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
            return rooms.snapshot(room, "host")

    @app.get("/api/rooms/{room_id}")
    async def get_room(room_id: str, request: Request):
        room = rooms.room_or_404(room_id)
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        actor = (
            "audience"
            if request.headers.get("x-showdown-view") == "audience"
            else auth.actor_for(room, token, request.cookies)
        )
        return rooms.snapshot(room, actor)

    @app.post("/api/rooms/{room_id}/commands")
    async def command(room_id: str, body: Command, request: Request):
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        return await rooms.execute(room_id, body, token, request.cookies, auth)
