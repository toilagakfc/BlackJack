# main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from infrastructure.database.mongodb import connect_mongo, close_mongo
from infrastructure.database.redis import connect_redis, close_redis
from presentation.sockets.server import socket_app
from presentation.sockets.handlers import *

# #import db
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await connect_mongo()
#     await connect_redis()
#     yield
#     await close_mongo()
#     await close_redis
# app = FastAPI(lifespan=lifespan)

app=FastAPI()
# gắn socket.io vào FastAPI
app.mount("/", socket_app)


@app.get("/health")
def health():
    return {"status": "ok"}