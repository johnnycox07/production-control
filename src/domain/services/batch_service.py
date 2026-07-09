import json
from datetime import datetime, timezone, date

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import BatchCreate, BatchUpdate, BatchResponse
from src.core.cache import cache
from src.data.models.batch import Batch
from src.data.repositories.batch_repository import BatchRepository
from src.domain.exceptions import BatchNotFoundError


class BatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = BatchRepository(session)

    async def create_batches(self, data: list[BatchCreate]) -> list[Batch]:
        created_ids = []

        for item in data:
            work_center = await self.batch_repo.get_or_create_work_center(
                identifier=item.work_center_id,
                name=item.work_center,
            )
            batch_data = item.model_dump(
                exclude={"work_center", "work_center_id"}
            )
            batch_data["work_center_id"] = work_center.id
            batch = await self.batch_repo.create(**batch_data)
            created_ids.append(batch.id)

        await self.session.commit()
        await cache.delete_pattern("batches_list:*")

        result = []
        for batch_id in created_ids:
            batch = await self.batch_repo.get_by_id_with_products(batch_id)
            result.append(batch)

        return result

    async def get_batch(self, batch_id: int) -> BatchResponse:
        key = f"batch_detail:{batch_id}"

        cached = await cache.get(key)

        if cached:
            return BatchResponse.model_validate_json(cached)
            
        batch = await self.batch_repo.get_by_id_with_products(batch_id)
        if batch is None:
            raise BatchNotFoundError(batch_id)

        response = BatchResponse.model_validate(batch)
        await cache.set(
            key,
            response.model_dump_json(),
            ttl=600,
        )

        return response

    async def update_batch(self, batch_id: int, data: BatchUpdate) -> BatchResponse:
        batch = await self.batch_repo.get_by_id_with_products(batch_id)
        if batch is None:
            raise BatchNotFoundError(batch_id)

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"work_center"},
        )

        if "is_closed" in update_data:
            if update_data["is_closed"] is True:
                update_data["closed_at"] = datetime.now(timezone.utc)
            else:
                update_data["closed_at"] = None

        if "work_center_id" in update_data:
            work_center = await self.batch_repo.get_or_create_work_center(
                identifier=update_data["work_center_id"],
                name=data.work_center or "",
            )
            update_data["work_center_id"] = work_center.id

        await self.batch_repo.update(batch_id, **update_data)
        await self.session.commit()
        await cache.delete(f"batch_detail:{batch_id}")
        await cache.delete_pattern("batches_list:*")

        updated_batch = await self.batch_repo.get_by_id_with_products(batch_id)
        return BatchResponse.model_validate(updated_batch)

    async def get_batches(
        self,
        is_closed: bool | None = None,
        batch_number: int | None = None,
        batch_date: date | None = None,
        work_center_id: int | None = None,
        shift: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[BatchResponse]:
        key = (
            f"batches_list:"
            f"{is_closed}:"
            f"{batch_number}:"
            f"{batch_date}:"
            f"{work_center_id}:"
            f"{shift}:"
            f"{offset}:"
            f"{limit}"
        )

        cached = await cache.get(key)

        if cached:
            data = json.loads(cached)
            return [
                BatchResponse.model_validate(item)
                for item in data
            ]

        batches = await self.batch_repo.get_filtered(
            is_closed=is_closed,
            batch_number=batch_number,
            batch_date=batch_date,
            work_center_id=work_center_id,
            shift=shift,
            offset=offset,
            limit=limit,
        )

        response = [
            BatchResponse.model_validate(batch)
            for batch in batches
        ]

        await cache.set(
            key,
            json.dumps(
                [item.model_dump(mode="json") for item in response]
            ),
            ttl=600,
        )

        return response