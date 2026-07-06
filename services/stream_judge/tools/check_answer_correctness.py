"""See plan section 6: this originally gated judgment on a per-line ASR
confidence score. That was removed — confirmed via WhisperLiveKit's own
docs/API.md and its Deepgram-compat source that no real confidence score
is provided anywhere (Deepgram-compat hardcodes 0.0). Enforcing that gate
would have made every call return "uncertain" unconditionally.

Uncertainty is now handled entirely by the Judge LLM's own three-way
verdict — the LLM decides "uncertain" from the CONTENT of the transcript
(garbled, incomplete, or ambiguous phrasing) rather than a numeric
pre-filter fed by data WhisperLiveKit doesn't actually provide.
"""

from typing import Literal

CorrectnessVerdict = Literal["correct", "incorrect", "uncertain"]


async def check_answer_correctness(
    question: str,
    expected_answer: str,
    student_utterance: str,
) -> CorrectnessVerdict:
    # TODO: wire up an actual LiteLLM call, e.g.:
    #   prompt = (
    #       f"Question: {question}\nExpected answer: {expected_answer}\n"
    #       f"Student said: {student_utterance}\n"
    #       "Is the student's answer correct, incorrect, or is the transcript too "
    #       "garbled/incomplete/ambiguous to judge fairly? "
    #       "Reply with exactly one word: correct, incorrect, or uncertain."
    #   )
    #   verdict = await call_llm(prompt)  # via shared LiteLLM proxy config
    #   return verdict.strip().lower()
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Stream Judge")
