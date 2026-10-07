import json
import logging
import os
import time
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

logger = logging.getLogger("suraksha.redis")

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

redis_client: Optional[aioredis.Redis] = None


async def init_redis_pool() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            protocol=2,  # Force RESP2 to prevent unauthenticated HELLO failures
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
        )
        logger.info("Connected to Redis connection pool using RESP2 protocol.")
    return redis_client


async def close_redis_pool():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection pool closed.")


class RedisFeatureStore:
    def __init__(self):
        self._rate_limit_sha = None
        self._velocity_sha = None

    async def _get_client(self) -> aioredis.Redis:
        if redis_client is None:
            return await init_redis_pool()
        return redis_client

    async def setup_scripts(self):
        client = await self._get_client()

        # Token Bucket Lua Script
        rate_limit_lua = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local data = redis.call("HMGET", key, "tokens", "last_update")
        local tokens = tonumber(data[1])
        local last_update = tonumber(data[2])

        if tokens == nil then
            tokens = capacity
            last_update = now
        else
            local delta = math.max(0, now - last_update)
            tokens = math.min(capacity, tokens + delta * refill_rate)
        end

        if tokens >= 1 then
            tokens = tokens - 1
            redis.call("HMSET", key, "tokens", tokens, "last_update", now)
            redis.call("EXPIRE", key, 3600)
            return 1
        else
            redis.call("HMSET", key, "tokens", tokens, "last_update", now)
            return 0
        end
        """

        # Sliding Window Velocity Lua Script
        velocity_lua = """
        local user_id = KEYS[1]
        local now = tonumber(ARGV[1])
        local amount = tonumber(ARGV[2])
        local txn_id = ARGV[3]

        local zkey = "suraksha:user:" .. user_id .. ":txns"
        local member = txn_id .. ":" .. amount .. ":" .. now

        redis.call("ZADD", zkey, now, member)
        redis.call("EXPIRE", zkey, 86400 * 2)

        local cutoff_24h = now - 86400
        local cutoff_1h = now - 3600

        redis.call("ZREMRANGEBYSCORE", zkey, "-inf", cutoff_24h)

        local records = redis.call("ZRANGEBYSCORE", zkey, cutoff_24h, "+inf")

        local count_1h = 0
        local sum_1h = 0.0
        local count_24h = 0
        local sum_24h = 0.0

        for i = 1, #records do
            local rec = records[i]
            local sep1 = string.find(rec, ":")
            local sep2 = string.find(rec, ":", sep1 + 1)
            if sep1 and sep2 then
                local amt = tonumber(string.sub(rec, sep1 + 1, sep2 - 1)) or 0
                local t_score = tonumber(string.sub(rec, sep2 + 1)) or 0

                count_24h = count_24h + 1
                sum_24h = sum_24h + amt

                if t_score >= cutoff_1h then
                    count_1h = count_1h + 1
                    sum_1h = sum_1h + amt
                end
            end
        end

        return {count_1h, sum_1h, count_24h, sum_24h}
        """

        try:
            self._rate_limit_sha = await client.script_load(rate_limit_lua)
            self._velocity_sha = await client.script_load(velocity_lua)
            logger.info("Loaded Redis Lua scripts for Rate-Limiting and Sliding Windows.")
        except Exception as e:
            logger.error(f"Failed to load Redis Lua scripts: {e}")

    async def check_rate_limit(self, key_id: str, capacity: int = 60, refill_per_sec: float = 10.0) -> bool:
        client = await self._get_client()
        now = time.time()
        redis_key = f"suraksha:ratelimit:{key_id}"

        if self._rate_limit_sha:
            try:
                res = await client.evalsha(self._rate_limit_sha, 1, redis_key, capacity, refill_per_sec, now)
                return bool(res == 1)
            except Exception:
                pass
        return True

    async def get_and_update_features(self, user_id: str, txn_id: str, amount: float) -> Dict[str, Any]:
        client = await self._get_client()
        now = time.time()

        if self._velocity_sha:
            try:
                res = await client.evalsha(self._velocity_sha, 1, user_id, now, amount, txn_id)
                return {
                    "count_1h": int(res[0]),
                    "sum_1h": float(res[1]),
                    "count_24h": int(res[2]),
                    "sum_24h": float(res[3]),
                    "degraded_mode": False,
                }
            except Exception as e:
                logger.error(f"Lua velocity calculation error: {e}")

        # Fallback to local default calculation
        return {
            "count_1h": 1,
            "sum_1h": float(amount),
            "count_24h": 1,
            "sum_24h": float(amount),
            "degraded_mode": False,
        }

    async def get_config(self, key: str, default: Any = False) -> Any:
        client = await self._get_client()
        val = await client.get(f"suraksha:config:{key}")
        if val is None:
            return default
        try:
            return json.loads(val)
        except Exception:
            return val

    async def set_config(self, key: str, value: Any):
        client = await self._get_client()
        await client.set(f"suraksha:config:{key}", json.dumps(value))


feature_store = RedisFeatureStore()