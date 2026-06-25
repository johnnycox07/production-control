from src.data.repositories.base_repository import BaseRepository
from src.data.models.batch import Batch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

class BatchRepository(BaseRepository[Batch]):
    def __init__(self, session: AsyncSession):
        super().__init__(Batch, session)

    async def get_filtered(
            self,
            is_closed: bool | None = None,
            batch_number: int | None = None,
            batch_date: date | None = None,
            work_center_id: int | None = None,
            shift: str | None = None,
            offset: int = 0,
            limit: int = 20
    ) -> list[Batch]:
        query = select(Batch)
        if is_closed is not None:
            query = query.where(Batch.is_closed == is_closed)

        if batch_number is not None:
            query = query.where(Batch.batch_number == batch_number)

        if batch_date is not None:
            query = query.where(Batch.batch_date == batch_date)

        if work_center_id is not None:
            query = query.where(Batch.work_center_id == work_center_id)

        if shift is not None:
            query = query.where(Batch.shift == shift)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())