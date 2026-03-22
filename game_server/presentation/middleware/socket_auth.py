# game_server/presentation/middleware/socket_auth.py
"""
Socket.IO JWT authentication middleware.

How it works
────────────
1. Client connects with:
       socket = io(url, { auth: { token: "<jwt>" } })
   or as a query param:
       io(url + "?token=<jwt>")

2. This middleware runs on every connect event (registered via sio.on("connect")).
   It extracts the token, decodes it, and stores player_id in the session.

3. All socket handlers retrieve the authenticated player_id with:
       player_id = await sio.get_session(sid)["player_id"]
   or via the helper get_player_id(sid) below.

4. If the token is missing or invalid the connection is rejected
   by returning False from the connect handler.

Registration (call once at startup, before any handlers):
    from presentation.middleware.socket_auth import register_auth_middleware
    register_auth_middleware(sio, auth_service)
"""
from __future__ import annotations

import logging

logger = logging.getLogger("SocketAuth")


def register_auth_middleware(sio, auth_service):
    """
    Attach the JWT validation hook to the given AsyncServer instance.
    Must be called before any @sio.event handlers are registered
    so that the connect handler set here fires first.
    """

    @sio.event
    async def connect(sid, environ, auth):
        """
        auth  — dict sent from client: { "token": "<jwt>" }
        environ — ASGI environ (also checked for ?token= query param as fallback)
        """
        token = _extract_token(auth, environ)

        if not token:
            logger.warning(f"Connection rejected (no token) — sid={sid}")
            return False  # reject connection

        try:
            player_id = auth_service.get_player_id_from_token(token)
        except ValueError:
            logger.warning(f"Connection rejected (invalid token) — sid={sid}")
            return False

        # Store player_id in the session for all subsequent events
        await sio.save_session(sid, {"player_id": player_id})
        logger.info(f"Authenticated — sid={sid} player_id={player_id}")
        return True  # accept

    @sio.event
    async def disconnect(sid):
        logger.info(f"Disconnected — sid={sid}")


def _extract_token(auth: dict | None, environ: dict) -> str | None:
    """Try auth dict first, then query string fallback."""
    if isinstance(auth, dict) and auth.get("token"):
        return auth["token"]

    # Query string fallback: ?token=<jwt>
    qs = environ.get("QUERY_STRING", "")
    for part in qs.split("&"):
        if part.startswith("token="):
            return part[len("token="):]

    return None


async def get_player_id(sio, sid: str) -> str:
    """
    Helper for handlers — retrieves the authenticated player_id from session.
    Raises ValueError('UNAUTHENTICATED') if session has no player_id.
    """
    session = await sio.get_session(sid)
    player_id = session.get("player_id") if session else None
    if not player_id:
        raise ValueError("UNAUTHENTICATED")
    return player_id