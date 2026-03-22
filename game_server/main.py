# main.py
import uvicorn
from fastapi import FastAPI
import asyncio
from config.setting import settings
from config.logging import setup_logging
from contextlib import asynccontextmanager
from infrastructure.database.mongodb import mongo
# from infrastructure.database.redis import connect_redis, close_redis
from infrastructure.repositories.player_account_repo_mongo import MongoPlayerAccountRepository
from application.services.auth_service import AuthService
from presentation.sockets.server import sio,socket_app
from presentation.middleware.socket_auth import register_auth_middleware
from presentation.api.auth_router import router as auth_router
from presentation.sockets.handlers import *

setup_logging()
#import db
@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo.connect()
    asyncio.create_task(mongo.monitor())
    # await connect_redis()
    yield
    await mongo.close()
    # await close_redis
app = FastAPI(lifespan=lifespan)
# ── REST API ──────────────────────────────────────────────────────────────
app.include_router(auth_router)
# ── Socket.IO ─────────────────────────────────────────────────────────────
_account_repo = MongoPlayerAccountRepository(mongo)
_auth_service = AuthService(
    account_repo=_account_repo,
    jwt_secret=settings.jwt_secret,
    jwt_algorithm=settings.jwt_algorithm,
    token_expire_minutes=settings.jwt_expire_minutes,
)
# Must be registered BEFORE any @sio.event handlers so the connect hook fires first
register_auth_middleware(sio, _auth_service)
 

app.mount("/socket.io", socket_app)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.app_port),
        log_level="info"
    )