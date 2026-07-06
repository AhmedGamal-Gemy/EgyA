"""See plan section 7.5 — Report Agent tools.

Closes the loop: attaches this session's report as context for the next
Setup Agent call. Plain HTTP call to Setup Agent's own endpoint (see plan
section 6/9 — A2A was considered and rejected for this hand-off; a direct
call is simpler and there's no cross-team/cross-language reason to need a
formal protocol here).
"""

import httpx

from shared.schemas.report import SessionReport

SETUP_AGENT_URL = "http://setup-agent:8001"


async def push_to_next_setup(report: SessionReport, next_session_id: str) -> None:
    async with httpx.AsyncClient() as client:
        # TODO: this assumes Setup Agent exposes an endpoint to receive a
        # previous report as context for a new session — not yet added to
        # setup_agent/main.py. For now this documents the intended call
        # shape; wire the actual endpoint alongside it.
        await client.post(
            f"{SETUP_AGENT_URL}/session/{next_session_id}/previous-report",
            json=report.model_dump(mode="json"),
        )
