# game_server/infrastructure/database/mongo_manager.py
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError, AutoReconnect

logger = logging.getLogger("mongo")


def _is_atlas(uri: str) -> bool:
    """Detect MongoDB Atlas URIs by scheme or hostname pattern."""
    return "mongodb+srv" in uri or "mongodb.net" in uri


class MongoManager:

    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.connected = False

    async def connect(self):
        """Attempt connection, retrying on transient failures.
        Raises immediately on configuration errors (bad URI, SRV failure, etc.)
        """
        atlas = _is_atlas(self.uri)

        while True:
            try:
                kwargs: dict = dict(
                    serverSelectionTimeoutMS=10_000,  # Atlas needs more time than local
                    connectTimeoutMS=20_000,
                    socketTimeoutMS=30_000,
                    retryWrites=True,
                )
                if atlas:
                    kwargs["tls"] = True
                    kwargs["tlsAllowInvalidCertificates"] = False

                self.client = AsyncIOMotorClient(self.uri, **kwargs)
                await self.client.admin.command("ping")

                self.db = self.client[self.db_name]
                self.connected = True
                logger.info(f"MongoDB connected ({'Atlas' if atlas else 'local'}) db={self.db_name}")
                return

            except ConfigurationError as exc:
                # Bad URI, SRV DNS failure, wrong auth mechanism — retrying won't help
                logger.error(f"MongoDB configuration error: {exc}")
                raise

            except ServerSelectionTimeoutError:
                self.connected = False
                logger.warning("MongoDB unreachable, retrying in 3 s…")
                await asyncio.sleep(3)

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_db(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            raise RuntimeError("MongoDB not connected — call connect() first")
        return self.db

    async def monitor(self):
        """Background health-check task — reconnects if ping fails."""
        while True:
            await asyncio.sleep(30)
            try:
                if self.client is None:
                    await self.connect()
                    continue

                await self.client.admin.command("ping")

                if not self.connected:
                    logger.info("MongoDB reconnected")
                self.connected = True

            except (ServerSelectionTimeoutError, AutoReconnect):
                if self.connected:
                    logger.warning("MongoDB connection lost")
                self.connected = False
                await self.connect()