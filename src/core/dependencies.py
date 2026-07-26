from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

def service_factory(service_cls):
    def _factory(session: AsyncSession = Depends(get_db)):
        return service_cls(session)

    return _factory