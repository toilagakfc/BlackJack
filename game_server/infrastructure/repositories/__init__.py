import os
from .room_repo_memory import InMemoryRoomRepository
from .room_repo_mongo import MongoRoomRepository
from .game_state_repo_mongo import MongoGameStateRepository
from .player_repo_mongo import MongoPlayerRepository
from config.setting import settings
from infrastructure.database.mongodb import mongo

def get_room_repository():
    room_storage = settings.ROOM_STORAGE
    if room_storage == "mongo":
        return MongoRoomRepository(mongo)

    return InMemoryRoomRepository()

def get_game_repository():
    game_storage = settings.GAME_STORAGE
    if game_storage == "redis":
        return InMemoryRoomRepository()

    return MongoGameStateRepository(mongo)

def get_player_repository():
    return MongoPlayerRepository(mongo)