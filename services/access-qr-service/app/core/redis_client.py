from redis.asyncio import Redis

from app.core.config import settings


redis_client: Redis = Redis.from_url(
    str(settings.REDIS_URL),
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


async def close_redis_client() -> None:
    await redis_client.aclose()