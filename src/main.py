from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from scripts.init_minio import initialize_minio_buckets
from src.api.v1.routers.analytics import router as analytics_router
from src.api.v1.routers.batches import router as batches_router
from src.api.v1.routers.products import router as products_router
from src.api.v1.routers.tasks import router as tasks_router
from src.api.v1.routers.webhooks import router as webhooks_router
from src.core.config import settings
from src.core.database import engine
from src.core.security import get_api_key


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_minio_buckets()
    yield
    await engine.dispose()

app = FastAPI(
    lifespan=lifespan,
    title="Production Control API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(batches_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(products_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(webhooks_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(tasks_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(analytics_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

@app.get("/health")
async def health():
    return {"status": "ok"}