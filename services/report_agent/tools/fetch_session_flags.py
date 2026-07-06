"""Thin wrapper tool, backed by raw redis-py — mirrors write_flag.py's
pattern on the Stream Judge side. See plan section 6a for the shared Flag
schema this reads back into.
"""

import redis.asyncio as redis

from shared.constants import REDIS_URL, REDIS_FLAG_KEY_PREFIX
from shared.schemas.flag import Flag

_client = redis.from_url(REDIS_URL, decode_responses=True)


async def fetch_session_flags(session_id: str) -> list[Flag]:
    key = f"{REDIS_FLAG_KEY_PREFIX}{session_id}"
    entries = await _client.xrange(key)
    flags = []
    for _, fields in entries:
        flags.append(Flag.model_validate_json(fields["data"]))
    return flags
