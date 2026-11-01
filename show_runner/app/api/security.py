from fastapi import Response

from ..config import valid_origin


def register(app):
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
