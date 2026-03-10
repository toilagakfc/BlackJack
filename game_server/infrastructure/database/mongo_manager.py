# infrastructure/database/mongo_manager.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError,AutoReconnect
import logging

logger = logging.getLogger("mongo")

class MongoManager:

    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.connected = False

    async def connect(self):

        while True:
            try:
                
                self.client = AsyncIOMotorClient(
                    self.uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=15000,
                    socketTimeoutMS=30000,
                )

                await self.client.admin.command("ping")

                self.db = self.client[self.db_name]
                self.connected = True
                
                logger.info("MongoDB connected")
                return

            except ServerSelectionTimeoutError:

                self.connected = False

                logger.info("MongoDB connection failed. retrying in 3 seconds")

    async def close(self):

        if self.client:
            self.client.close()
            logger.info("Mongo closed")

    def get_db(self) -> AsyncIOMotorDatabase:

        if self.db is None:
            raise RuntimeError("Mongo not connected")

        return self.db
    
    async def monitor(self):
        while True:

            try:
                if self.client is None:
                    await self.connect()
                    continue

                await self.client.admin.command(
                    "ping"
                )

                if not self.connected:
                    logger.info("MongoDB reconnected")
                self.connected = True

            except (ServerSelectionTimeoutError, AutoReconnect):

                if self.connected:
  
                    logger.info("MongoDB reconnected")
                self.connected = False

                logger.info("Trying to connect MongoDB...")
                await self.connect()

