"""See plan section 7.5 — Stream Judge tools."""

from typing import Literal

from shared.enums.flag_type import AudienceLevel

PacingVerdict = Literal["on_pace", "too_fast", "too_slow"]
ClarityVerdict = Literal["clear", "unclear_for_level"]


async def assess_pacing_clarity(
    transcript_line: str,
    audience_level: AudienceLevel,
) -> tuple[PacingVerdict, ClarityVerdict]:
    # TODO: wire up a LiteLLM call — this needs more than one line of
    # context in practice (pacing is a judgment over a window of time, not
    # a single utterance); consider passing recent transcript history once
    # this is actually implemented, not just the latest line.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Stream Judge")
