from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"

client: AsyncIOMotorClient | None = None
db = None

async def connect_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["game_server"]


async def close_mongo():
    global client
    if client:
        client.close()