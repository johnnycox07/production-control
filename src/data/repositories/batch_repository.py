from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.batch import Batch
from src.data.models.work_center import WorkCenter
from src.data.repositories.base_repository import BaseRepository


class BatchRepository(BaseRepository[Batch]):
    def __init__(self, session: AsyncSession):
        super().__init__(Batch, session)

    async def get_or_create_work_center(
            self, identifier: str, name: str
    ) -> WorkCenter:
        result = await self.session.execute(
            select(WorkCenter).where(WorkCenter.identifier == identifier)
        )
        work_center = result.scalar_one_or_none()
        if not work_center:
            work_center = WorkCenter(identifier=identifier, name=name)
            self.session.add(work_center)
            await self.session.flush()
        return work_center

    async def get_by_id_with_products(self, batch_id: int) -> Batch | None:
        result = await self.session.execute(
            select(Batch)
            .where(Batch.id == batch_id)
            .options(selectinload(Batch.products))
        )
        return result.scalar_one_or_none()

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
        query = select(Batch).options(selectinload(Batch.products))

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