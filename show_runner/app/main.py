"""Application composition and lifecycle. Run with app.main:app."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from .api import auth as auth_api
from .api import frontend, security, websocket
from .api import rooms as rooms_api
from .config import database_path, host_password, load_questions
from .services.auth import AuthService
from .services.rooms import RoomService
from .storage.sqlite import Store


def create_app(db_path=None, password=None, questions=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.password = host_password(password)
        app.state.questions = load_questions(questions)
        app.state.store = Store(database_path(db_path))
        app.state.rooms = app.state.store.all()
        app.state.lock = asyncio.Lock()
        app.state.clients = {}
        app.state.attempts = {}
        task = asyncio.create_task(rooms.tick())
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

    app = FastAPI(title="Rats on the Rift", version="0.1.1", lifespan=lifespan)
    auth = AuthService(app)
    rooms = RoomService(app)
    security.register(app)
    auth_api.register(app, auth)
    rooms_api.register(app, auth, rooms)
    websocket.register(app, auth, rooms)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.1"}

    frontend.register(app)
    return app


app = create_app()
