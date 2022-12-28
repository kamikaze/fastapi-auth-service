import redis.asyncio

from fastapi_auth_service.conf import settings


redis_db = redis.asyncio.from_url(settings.redis_dsn, decode_responses=True)
