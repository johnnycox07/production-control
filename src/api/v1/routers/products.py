from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.product import ProductCreate, ProductResponse
from src.core.dependencies import get_db
from src.core.exceptions import BatchNotFoundError
from src.domain.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

async def get_product_service(
        session: AsyncSession = Depends(get_db)
) -> ProductService:
    return ProductService(session)

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_products(
        data: ProductCreate,
        service: ProductService = Depends(get_product_service),
):
    try:
        return await service.create_product(data)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found")
