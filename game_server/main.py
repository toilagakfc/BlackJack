# main.py
import uvicorn
from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
from infrastructure.database.mongodb import mongo
from infrastructure.database.redis import connect_redis, close_redis
from presentation.sockets.server import socket_app
from presentation.sockets.handlers import *
from config.setting import settings
from config.logging import setup_logging
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