from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastapi_auth_service.conf import settings

metadata = MetaData()
Base = declarative_base(metadata=metadata)
engine = create_async_engine(settings.db_dsn)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def is_healthy(pg) -> bool:
    return await pg.fetchval('SELECT 1 FROM alembic_version;') == 1
