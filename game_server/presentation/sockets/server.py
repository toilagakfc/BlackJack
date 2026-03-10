# presentation/sockets/server.py

import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    # logger=True,
    # engineio_logger=True
)

socket_app = socketio.ASGIApp(sio)


