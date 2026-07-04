from fastapi import FastAPI

from src.api.v1.routers.batches import router as batches_router

app = FastAPI(
    title="Production Control API",
    version="1.0.0",
)

app.include_router(batches_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}