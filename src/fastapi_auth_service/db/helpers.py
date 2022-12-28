import logging

import sqlalchemy as sa
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth_service.api.users import create_user
from fastapi_auth_service.api.v1.schemas import UserCreate
from fastapi_auth_service.db.models import User

logger = logging.getLogger()


async def bootstrap_user(session: AsyncSession, settings):
    user_count = await session.execute(sa.select([sa.func.count(User.id)]))

    if user_count.scalar() == 0:
        logger.warning('No users in database')

        if settings.bootstrap_user_email:
            logger.info('Bootstrapping a user in database')

            try:
                await create_user(
                    UserCreate(
                        username=settings.bootstrap_user_email,
                        email=settings.bootstrap_user_email,
                        password=settings.bootstrap_user_password.get_secret_value(),
                        is_superuser=True,
                        is_active=True,
                        is_verified=True
                    )
                )
                logger.debug(f'Bootstrap user: {settings.bootstrap_user_email}')
            except UserAlreadyExists:
                logger.warning(f'User {settings.bootstrap_user_email} already exist')
