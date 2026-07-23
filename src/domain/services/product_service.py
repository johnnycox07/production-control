from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.product import ProductCreate
from src.core.exceptions import BatchNotFoundError, ProductNotFoundError, ProductAlreadyAggregatedError
from src.data.models.product import Product
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = BatchRepository(session)
        self.product_repo = ProductRepository(session)

    async def create_product(self, data: ProductCreate):
        batch = await self.batch_repo.get_by_id(data.batch_id)
        if batch is None:
            raise BatchNotFoundError(data.batch_id)

        product = await self.product_repo.create(**data.model_dump())
        await self.session.commit()
        return product

    async def aggregate_product(
            self, batch_id: int, unique_code: str
    ) -> Product:
        product = await self.product_repo.get_by_unique_code(batch_id, unique_code)
        if product is None:
            raise ProductNotFoundError(unique_code)

        if product.is_aggregated:
            raise ProductAlreadyAggregatedError(unique_code)

        product = await self.product_repo.update(
            product.id,
            is_aggregated=True,
            aggregated_at=datetime.now(timezone.utc),
        )
        await self.session.commit()
        return product