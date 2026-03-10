import os
from .room_repo_memory import InMemoryRoomRepository
from .room_repo_mongo import MongoRoomRepository
from config.setting import settings
from infrastructure.database.mongodb import mongo
def get_room_repository():

    storage = settings.ROOM_STORAGE
    if storage == "mongo":
        return MongoRoomRepository(mongo)

    return InMemoryRoomRepository()