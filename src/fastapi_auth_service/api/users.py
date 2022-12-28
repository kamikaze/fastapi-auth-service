import contextlib
import logging
import uuid
from typing import Optional, AsyncGenerator

from fastapi import Request, Depends
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth_service.api.v1.schemas import UserCreate, UserUpdate
from fastapi_auth_service.conf import settings
from fastapi_auth_service.db import async_session_maker
from fastapi_auth_service.db.models import User

logger = logging.getLogger()
context = CryptContext(schemes=['argon2', 'django_pbkdf2_sha256', 'django_pbkdf2_sha1', 'django_bcrypt'],
                       deprecated='auto')
password_helper = PasswordHelper(context)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth_secret
    verification_token_secret = settings.auth_secret

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f'User {user.id} has registered.')

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(f'User {user.id} has forgot their password. Reset token: {token}')

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(f'Verification requested for user {user.id}. Verification token: {token}')


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db, password_helper)


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(user: UserCreate):
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                try:
                    user = await user_manager.create(user)
                except UserAlreadyExists:
                    logger.warning(f'User {user.email} already exists')
                else:
                    logger.info(f'User created {user}')


async def update_user(user_id: str, user: UserUpdate):
    user.id = user_id

    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                r = await user_manager.update(user)

                logger.info(f'Updated user: {r}')

    return user
