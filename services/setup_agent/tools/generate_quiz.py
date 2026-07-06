"""See plan section 7.5 — Setup Agent tools.

IMPORTANT constraint (see plan section 6a): quiz questions/expected answers
must stay short and discrete (not open-ended), because Stream Judge's
check_answer_correctness compares a spoken transcript against
expected_answer — that's only tractable for short factual answers, not
open-ended discussion. Enforce this in the prompt, not just in a docstring.
"""

from shared.enums.flag_type import AudienceLevel
from shared.schemas.session_package import QuizQuestion


async def generate_quiz(topic: str, audience_level: AudienceLevel) -> list[QuizQuestion]:
    # TODO: wire up a LiteLLM call. Prompt MUST instruct the model to produce
    # short-answer/discrete questions only (e.g. "answer in one word or a
    # short phrase"), not open-ended/essay-style questions.
    raise NotImplementedError("Wire up the LiteLLM call — see plan section 6, Setup Agent")
