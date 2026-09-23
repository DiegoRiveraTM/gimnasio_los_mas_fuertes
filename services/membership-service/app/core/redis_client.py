import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(
    str(settings.REDIS_URL),
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)