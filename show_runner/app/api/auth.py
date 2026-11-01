import secrets
import time

from fastapi import HTTPException, Request, Response

from ..config import secure_cookie
from ..models.requests import Login


def register(app, auth):
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
            f"{expiry}.{auth.signature(expiry)}",
            httponly=True,
            samesite="strict",
            max_age=43200,
            secure=secure_cookie(),
        )
        return {"ok": True}

    @app.post("/api/logout")
    async def logout(response: Response):
        response.delete_cookie("showdown_host")
        return {"ok": True}
