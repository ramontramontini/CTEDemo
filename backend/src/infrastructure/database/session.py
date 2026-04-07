"""Async SQLAlchemy session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
