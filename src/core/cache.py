import redis.asyncio as aioredis

from src.core.config import settings

redis_client = aioredis.from_url(
    settings.redis_url,
    decode_responses=True,
)

class RedisCache:
    def __init__(self, client):
        self.client = client

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


cache = RedisCache(redis_client)