import redis.asyncio as redis

redis_client: redis.Redis | None = None


async def connect_redis():
    global redis_client
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )


async def close_redis():
    if redis_client:
        await redis_client.close()