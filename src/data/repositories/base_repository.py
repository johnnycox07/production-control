from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Generic, TypeVar
from ...core.database import Base
from sqlalchemy import select


T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> T | None:
        result = await self.session.get(self.model, id)
        return result

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs) -> T | None:
        obj = await self.session.get(self.model, id)
        if not obj:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        obj = await self.session.get(self.model, id)
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True


    async def get_all(
            self, offset: int = 0, limit: int = 20
    ) -> list[T]:
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())