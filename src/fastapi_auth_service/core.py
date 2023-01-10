import gettext
import logging
from pathlib import Path
from typing import Mapping

import sqlalchemy as sa
from fastapi_pagination import Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth_service.api.v1.schemas import UserItem
from fastapi_auth_service.db.models import UserGroup, User

logger = logging.getLogger(__name__)
t = gettext.translation('base', Path(Path(__file__).parent, 'locale'), fallback=True, languages=['lv_LV'])
_ = t.gettext


async def get_users(session: AsyncSession, search: Mapping[str, str] | None = None,
                    order_by: str | None = None) -> Page[UserItem]:
    query = sa.select([User])
    result = await paginate(session, query)

    return result


async def get_user(session: AsyncSession, user_id: str) -> UserItem:
    query = sa.select([User]).where(User.id == user_id)

    return await session.execute(query)


async def get_user_groups(session: AsyncSession, search: Mapping[str, str] | None = None,
                          order_by: str | None = None) -> Page[UserGroup]:
    query = sa.select([UserGroup]).order_by(UserGroup.name)
    result = await paginate(session, query)

    return result
