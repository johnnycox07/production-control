from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.product import Product
from src.data.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_by_unique_code(
        self, batch_id: int, unique_code: str
    ) -> Product | None:
        result = await self.session.execute(
            select(Product).where(
                Product.batch_id == batch_id,
                Product.unique_code == unique_code,
            )
        )
        return result.scalar_one_or_none()