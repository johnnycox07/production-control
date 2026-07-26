from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Dependency для проверки API ключа.
    auto_error=False — не бросаем ошибку автоматически,
    обрабатываем сами чтобы вернуть понятное сообщение.
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key missing. Pass X-API-Key header.",
        )
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )
    return api_key