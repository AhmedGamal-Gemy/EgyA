"""Thin wrapper tool, backed by raw redis-py (see plan section 3 — Redis MCP
was considered and rejected as the same kind of overkill as A2A).

Schema enforcement happens here: this function's signature only accepts a
typed Flag, so the LLM tool-calling it can't write anything malformed — see
plan section 6a.
"""

import redis.asyncio as redis

from shared.constants import REDIS_URL, REDIS_FLAG_KEY_PREFIX
from shared.schemas.flag import Flag

_client = redis.from_url(REDIS_URL, decode_responses=True)


async def write_flag(flag: Flag) -> None:
    key = f"{REDIS_FLAG_KEY_PREFIX}{flag.session_id}"
    await _client.xadd(key, {"data": flag.model_dump_json()})
