import logging
import uuid
from functools import wraps
from inspect import signature

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import ORJSONResponse
from fastapi_pagination import Page
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, CookieTransport
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth_service import core
from fastapi_auth_service.api import users
from fastapi_auth_service.api.users import get_user_manager, get_async_session
from fastapi_auth_service.api.v1.schemas import (
    UserCreate, UserUpdate, UserItem, UserGroup, UserRead
)
from fastapi_auth_service.authentication import RedisStrategy
from fastapi_auth_service.conf import settings
from fastapi_auth_service.db import engine
from fastapi_auth_service.db.models import User
from fastapi_auth_service.db.redis import redis_db
from fastapi_auth_service.helpers import connect_to_db

logger = logging.getLogger(__name__)
router = APIRouter()
cookie_transport = CookieTransport(cookie_max_age=3600)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.auth_secret, lifetime_seconds=3600)


def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(redis_db, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(name='cluserauth', transport=cookie_transport, get_strategy=get_redis_strategy)
auth_backends = [auth_backend, ]
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    auth_backends
)
get_current_user = fastapi_users.current_user(active=True)
auth_router = fastapi_users.get_auth_router(auth_backend, requires_verification=True)
users_router = fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True)


@router.on_event('startup')
async def startup():
    await connect_to_db(engine)


@router.on_event('shutdown')
async def shutdown():
    logger.warning('Not Implemented')
    # await database.disconnect()


def _handle_exceptions_helper(status_code, *args):
    if args:
        raise HTTPException(status_code=status_code, detail=args[0])
    else:
        raise HTTPException(status_code=status_code)


def handle_exceptions(func):
    signature(func)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PermissionError as e:
            return _handle_exceptions_helper(status.HTTP_401_UNAUTHORIZED, *e.args)
        except LookupError as e:
            return _handle_exceptions_helper(status.HTTP_404_NOT_FOUND, *e.args)
        except ValueError as e:
            return _handle_exceptions_helper(status.HTTP_400_BAD_REQUEST, *e.args)

    return wrapper


@router.get('/users', response_class=ORJSONResponse, tags=['Admin'])
@handle_exceptions
async def get_users(search: Json | None = None, order_by: str | None = None, user=Depends(get_current_user),
                    session: AsyncSession = Depends(get_async_session)) -> Page[UserItem]:
    if user.is_superuser:
        return await core.get_users(session, search, order_by)

    raise HTTPException(status_code=403)


@router.post('/users', response_class=ORJSONResponse, tags=['Admin'])
@handle_exceptions
async def create_user(new_user: UserCreate, user=Depends(get_current_user)) -> UserItem:
    if user.is_superuser:
        created_user = await users.create_user(new_user)

        return created_user

    raise HTTPException(status_code=403)


@router.get('/user-groups', response_class=ORJSONResponse, tags=['Admin'])
@handle_exceptions
async def get_user_groups(search: Json | None = None, order_by: str | None = None, user=Depends(get_current_user),
                          session: AsyncSession = Depends(get_async_session)) -> Page[UserGroup]:
    if user.is_active:
        return await core.get_user_groups(session, search, order_by)

    raise HTTPException(status_code=403)
