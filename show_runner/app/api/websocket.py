import asyncio
from contextlib import suppress

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..config import valid_origin


def register(app, auth, rooms):
    @app.websocket("/api/rooms/{room_id}/live")
    async def live(ws: WebSocket, room_id: str):
        if not valid_origin(ws.headers.get("origin"), ws.headers.get("host")):
            await ws.close(code=1008)
            return
        await ws.accept()
        registered = False
        try:
            credentials = await asyncio.wait_for(ws.receive_json(), timeout=5)
            if not isinstance(credentials, dict) or not isinstance(
                credentials.get("token", ""), str
            ):
                await ws.close(code=1008)
                return
            async with app.state.lock:
                room = rooms.room_or_404(room_id)
                actor = (
                    "audience"
                    if credentials.get("view") == "audience"
                    else auth.actor_for(room, credentials.get("token", ""), ws.cookies)
                )
                clients = app.state.clients.setdefault(room_id, {})
                if len(clients) >= 24:
                    await ws.close(code=1013)
                    return
                clients[ws] = actor
                registered = True
                await rooms.broadcast(room)
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
                    await rooms.broadcast(app.state.rooms[room_id])
