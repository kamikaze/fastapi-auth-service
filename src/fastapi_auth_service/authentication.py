import secrets

from fastapi_users import exceptions, models
from fastapi_users.authentication.strategy import redis
from fastapi_users.manager import BaseUserManager


class RedisStrategy(redis.RedisStrategy):
    async def read_token(
        self, token: str | None, user_manager: BaseUserManager[models.UP, models.ID]
    ) -> models.UP | None:
        if token is None:
            return None

        user_id = await self.redis.get(f"{self.key_prefix}{token}")
        if user_id is None:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID):
            return None

    async def write_token(self, user: models.UP) -> str:
        token = secrets.token_urlsafe()
        await self.redis.set(f"{self.key_prefix}{token}", str(user.id), ex=self.lifetime_seconds)

        return token
