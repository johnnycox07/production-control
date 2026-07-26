from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends

from src.api.v1.schemas.product import ProductCreate, ProductResponse
from src.core.dependencies import service_factory
from src.domain.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

ProductServiceDep = Annotated[
    ProductService,
    Depends(service_factory(ProductService)),
]

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_products(
        data: ProductCreate,
        service: ProductServiceDep,
):
    return await service.create_product(data)

