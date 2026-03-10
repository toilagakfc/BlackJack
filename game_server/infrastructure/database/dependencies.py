# infrastructure/database/dependencies.py
from infrastructure.database.mongodb import mongo
from motor.motor_asyncio import AsyncIOMotorDatabase


def get_db() -> AsyncIOMotorDatabase:
    return mongo.get_db()