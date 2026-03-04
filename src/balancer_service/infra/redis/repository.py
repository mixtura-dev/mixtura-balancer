from redis.asyncio import Redis


class RedisRepository:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def _get_dict_by_key(self, key: str) -> dict | None:
        response = await self.redis.hgetall(key)  # type: ignore
        if not response:
            return None
        return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in
                response.items()}

    async def _get_element_by_key(self, key: str) -> str | None:
        response = await self.redis.get(key)
        if not response:
            return None
        return response.decode() if isinstance(response, bytes) else response

    def _get_draft_key(self, draft_id: str) -> str:
        return f"balance:draft:{draft_id}"

    def _get_balance_key(self, draft_id: str, balance_id: str) -> str:
        return f"balance:draft:{draft_id}:result:{balance_id}"

    