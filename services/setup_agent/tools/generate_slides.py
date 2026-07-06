"""See plan section 7.5 — Setup Agent tools."""

from shared.enums.flag_type import AudienceLevel


async def generate_slides(topic: str, audience_level: AudienceLevel, goals: list[str]) -> list[str]:
    # TODO: wire up a LiteLLM call via the agent's model (see agent.py),
    # prompting for slide content tailored to audience_level and goals.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Setup Agent")
