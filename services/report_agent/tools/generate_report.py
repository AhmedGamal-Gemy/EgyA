"""See plan section 7.5 — Report Agent tools."""

from shared.schemas.flag import Flag
from shared.schemas.report import FlagSummary, SessionReport


async def generate_report(
    session_id: str,
    flags: list[Flag],
    flag_summary: list[FlagSummary],
) -> SessionReport:
    # TODO: wire up a LiteLLM call that turns the raw flags + summary into
    # the structured SessionReport fields (what_confused_students,
    # wrong_answers, disengaged_speakers, reinforcement_needed,
    # delivery_adjustments, narrative_summary). This is the one place in
    # the whole system where LLM-generated prose genuinely adds value (see
    # plan section 6a's templated-vs-generated message decision) — use it
    # here for narrative_summary specifically.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Report Agent")
