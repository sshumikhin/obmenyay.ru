import asyncio
import redis.asyncio as aioredis
import redis.exceptions

from .config import CONNECTION_URL

__all__ = ["redis_client"]


class RedisClient:

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if getattr(self, 'connection', None) is None:
            self.connection = aioredis.from_url(
                url=CONNECTION_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def get(self, key):
        data_type = await self.connection.type(key)
        if data_type == b'hash':
            return await self.connection.hgetall(key)

        return await self.connection.get(key)

    async def set(self, key, value):
        if isinstance(value, dict):
            await self.connection.hset(key, mapping=value)
            return
        await self.connection.set(key, value)

    async def delete(self, key):
        await self.connection.delete(key)
    #
    # def __del__(self):
    #     self.connection.aclose()


redis_client = RedisClient()

