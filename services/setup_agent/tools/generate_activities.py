"""See plan section 7.5 — Setup Agent tools."""

from shared.enums.flag_type import AudienceLevel
from shared.schemas.session_package import Activity


async def generate_activities(topic: str, audience_level: AudienceLevel) -> list[Activity]:
    # TODO: wire up a LiteLLM call, activity/exercise definitions.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Setup Agent")
