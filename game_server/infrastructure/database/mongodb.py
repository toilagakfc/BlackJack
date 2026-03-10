# infrastructure/database/mongo.py
from infrastructure.database.mongo_manager import MongoManager
from config.setting import settings

MONGO_URI = settings.mongo_uri

mongo = MongoManager(
    uri=MONGO_URI,
    db_name=settings.mongo_db
)