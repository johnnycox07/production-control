from src.data.repositories.base_repository import BaseRepository
from src.data.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)