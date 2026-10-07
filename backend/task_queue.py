import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
import redis.asyncio as aioredis
from database import store_transaction_and_flag_safe, log_audit_entry_safe
from redis_store import init_redis_pool

logger = logging.getLogger("suraksha.queue")

STREAM_KEY = "suraksha:stream:events"
CONSUMER_GROUP = "suraksha:workers:persistence"
CONSUMER_NAME = "worker_core_01"


class DurableTaskQueue:
    def __init__(self):
        self.redis: aioredis.Redis = None

    async def initialize(self):
        self.redis = await init_redis_pool()
        try:
            # Create stream consumer group if it doesn't already exist
            await self.redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info("Initialized Redis Stream consumer group.")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                pass  # Group already initialized
            else:
                logger.error(f"Error initializing stream group: {e}")

    async def enqueue(self, event_type: str, payload: Dict[str, Any]):
        """Durable append to Redis Stream. Persists even if app crashes."""
        if not self.redis:
            self.redis = await init_redis_pool()

        event_body = {
            "type": event_type,
            "payload": json.dumps(payload),
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }
        msg_id = await self.redis.xadd(STREAM_KEY, event_body)
        return msg_id

    async def process_next_batch(self, count: int = 10):
        """Worker consumption loop with explicit ACK."""
        if not self.redis:
            self.redis = await init_redis_pool()

        try:
            entries = await self.redis.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_KEY: ">"},
                count=count,
                block=1000,
            )
            if not entries:
                return 0

            for stream, messages in entries:
                for msg_id, data in messages:
                    # Robust extraction: handles both decode_responses=True (str) and False (bytes)
                    raw_type = data.get("type") if "type" in data else data.get(b"type", "")
                    event_type = raw_type.decode("utf-8") if isinstance(raw_type, bytes) else str(raw_type)

                    raw_payload = data.get("payload") if "payload" in data else data.get(b"payload", "{}")
                    payload_str = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else str(raw_payload)
                    payload = json.loads(payload_str)

                    try:
                        if event_type == "TRANSACTION_RECORD":
                            await store_transaction_and_flag_safe(
                                txn=payload["txn"],
                                result=payload["result"],
                                is_shadow=payload.get("is_shadow", False),
                            )
                        elif event_type == "AUDIT_LOG":
                            await log_audit_entry_safe(
                                user_id=payload["user_id"],
                                accessor=payload["accessor"],
                                access_type=payload["access_type"],
                                purpose=payload["purpose"],
                            )

                        # Explicit acknowledgment
                        await self.redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    except Exception as err:
                        logger.error(f"Failed processing stream message {msg_id}: {err}", exc_info=True)

            return len(entries[0][1])
        except Exception as e:
            logger.error(f"Queue processor error: {e}")
            return 0


durable_queue = DurableTaskQueue()


async def queue_worker_loop():
    """Background worker daemon running alongside or independent of API."""
    logger.info("Starting background persistence stream worker...")
    await durable_queue.initialize()
    while True:
        try:
            processed = await durable_queue.process_next_batch(count=20)
            if processed == 0:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("Worker loop gracefully shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker iteration failure: {e}")
            await asyncio.sleep(1)