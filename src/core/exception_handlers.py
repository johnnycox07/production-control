import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    BatchNotFoundError,
    ProductAlreadyAggregatedError,
    ProductNotFoundError,
    WebhookNotFoundError,
)

logger = logging.getLogger(__name__)

EXC_STATUS_MAP = {
    BatchNotFoundError: 404,
    ProductNotFoundError: 404,
    WebhookNotFoundError: 404,
    ProductAlreadyAggregatedError: 409,
}


def register_exception_handlers(app):
    for exc_cls, status in EXC_STATUS_MAP.items():
        app.add_exception_handler(
            exc_cls,
            lambda req, exc, status=status: JSONResponse(
                status_code=status, content={"detail": str(exc)}
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})