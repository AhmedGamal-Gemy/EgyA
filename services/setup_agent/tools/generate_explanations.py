"""See plan section 7.5 — Setup Agent tools."""

from shared.enums.flag_type import AudienceLevel


async def generate_explanations(topic: str, audience_level: AudienceLevel) -> list[str]:
    # TODO: wire up a LiteLLM call, level-tailored explanation text.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Setup Agent")
