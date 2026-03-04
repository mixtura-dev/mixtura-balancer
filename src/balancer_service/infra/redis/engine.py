import contextlib
from typing import AsyncIterator

from redis.asyncio import ConnectionPool, Redis


class RedisSessionManager:
    def __init__(self, url: str):
        self._url = url
        self._pool: ConnectionPool | None = ConnectionPool.from_url(self._url)

    async def close(self):
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None

    async def reopen(self):
        if self._pool is None:
            self._pool = ConnectionPool.from_url(self._url)

    async def connect(self):
        if self._pool is None:
            self._pool = ConnectionPool.from_url(self._url)

    @contextlib.asynccontextmanager
    async def client(self) -> AsyncIterator[Redis]:
        if self._pool is None:
            self._pool = ConnectionPool.from_url(self._url)
        client = Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            await client.aclose()

    @property
    async def opened(self) -> bool:
        return self._pool is not None
