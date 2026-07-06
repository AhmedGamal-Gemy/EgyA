from typing import List, Optional

from pydantic import BaseModel

from shared.enums.flag_type import AudienceLevel


class QuizQuestion(BaseModel):
    question: str
    expected_answer: str
    # keep answers short/discrete for the MVP — see plan section 6:
    # correctness-checking only works reliably for short/discrete answers,
    # not open-ended discussion.


class Activity(BaseModel):
    title: str
    instructions: str


class SessionPackage(BaseModel):
    """Setup Agent's output. Also Stream Judge's session-config input at
    kickoff — this is the direct dependency that makes answer-correctness
    checking possible (Stream Judge needs the expected answers)."""

    session_id: str
    topic: str
    audience_level: AudienceLevel
    goals: List[str]

    slides: List[str]
    explanations: List[str]
    activities: List[Activity]
    quiz: List[QuizQuestion]

    # populated only on sessions after the first, from the previous
    # session's report (cross-session memory, closes the loop)
    previous_session_report_summary: Optional[str] = None
