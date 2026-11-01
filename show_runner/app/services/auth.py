import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException


class AuthService:
    def __init__(self, app):
        self.app = app

    def signature(self, value):
        return hmac.new(
            self.app.state.password.encode(), value.encode(), hashlib.sha256
        ).hexdigest()

    def host_authenticated(self, cookies):
        token = cookies.get("showdown_host", "")
        try:
            expiry, sig = token.split(".", 1)
            return int(expiry) > time.time() and hmac.compare_digest(sig, self.signature(expiry))
        except (ValueError, TypeError):
            return False

    def actor_for(self, room, token, cookies):
        # Explicit contestant credentials take priority when testing seats in the host browser.
        if token:
            for index, invite in enumerate(room["invites"]):
                if secrets.compare_digest(invite.encode(), token.encode()):
                    return str(index)
            raise HTTPException(403, "Invalid contestant link")
        if self.host_authenticated(cookies):
            return "host"
        return "audience"
