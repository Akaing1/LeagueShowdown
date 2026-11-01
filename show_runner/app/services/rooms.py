import asyncio
import time
from contextlib import suppress
from copy import deepcopy

from fastapi import HTTPException, WebSocketDisconnect

from ..games.who_am_i import rules as engine


class RoomService:
    def __init__(self, app):
        self.app = app

    def room_or_404(self, room_id):
        room = self.app.state.rooms.get(room_id)
        if room is None:
            raise HTTPException(404, "Show not found")
        return room

    def snapshot(self, room, actor):
        state = engine.view(room["game"], actor)
        state.update(
            room_id=room["id"],
            revision=room["revision"],
            you=actor,
            server_time=time.time(),
            online=[
                p
                for p in ["0", "1", "2"]
                if p in self.app.state.clients.get(room["id"], {}).values()
            ],
        )
        if actor == "host":
            state.update(invites=room["invites"], can_undo=bool(room["history"]))
        return state

    async def send(self, ws, state):
        try:
            await asyncio.wait_for(ws.send_json(state), timeout=2)
        except (WebSocketDisconnect, TimeoutError, RuntimeError, OSError):
            for clients in self.app.state.clients.values():
                clients.pop(ws, None)
            with suppress(Exception):
                await ws.close(code=1011)

    async def broadcast(self, room):
        clients = list(self.app.state.clients.get(room["id"], {}).items())
        await asyncio.gather(*(self.send(ws, self.snapshot(room, actor)) for ws, actor in clients))

    def commit(self, previous, game, command_id=None, undo=False):
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
        self.app.state.store.save(room)
        self.app.state.rooms[room["id"]] = room
        return room

    async def tick(self):
        while True:
            await asyncio.sleep(0.25)
            async with self.app.state.lock:
                for room in list(self.app.state.rooms.values()):
                    game = deepcopy(room["game"])
                    if engine.expire(game):
                        updated = self.commit(room, game)
                        await self.broadcast(updated)

    async def execute(self, room_id, body, token, cookies, auth):
        async with self.app.state.lock:
            room = self.room_or_404(room_id)
            actor = auth.actor_for(room, token, cookies)
            if actor == "audience":
                raise HTTPException(403, "Contestant or host access required")
            # Deduplication is scoped to the actor, and checked before revision validation.
            command_id = f"{actor}:{body.id}"
            if command_id in room["commands"]:
                return self.snapshot(room, actor)
            game = deepcopy(room["game"])
            if engine.expire(game):
                room = self.commit(room, game)
                await self.broadcast(room)
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
            room = self.commit(room, game, command_id, undo=undo)
            await self.broadcast(room)
            return self.snapshot(room, actor)
