"""See plan section 7.5 — Stream Judge tools."""


async def detect_confusion(transcript_line: str) -> bool:
    # TODO: wire up a LiteLLM call (or a cheaper rule-based first pass —
    # e.g. keyword/question-pattern matching for "I don't understand",
    # "wait, what?", repeated clarifying questions — before reaching for an
    # LLM call on every single line, given hackathon time/cost pressure).
    raise NotImplementedError("Wire up detection logic — see plan section 6, Stream Judge")
