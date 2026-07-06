from typing import List

from pydantic import BaseModel

from shared.enums.flag_type import FlagType


class FlagSummary(BaseModel):
    flag_type: FlagType
    count: int
    examples: List[str] = []  # a few representative flag messages, not all of them


class SessionReport(BaseModel):
    session_id: str

    what_confused_students: List[str]
    wrong_answers: List[str]          # "question — how many times missed" style strings
    disengaged_speakers: List[str]    # speaker_ids flagged for disengagement

    reinforcement_needed: List[str]
    delivery_adjustments: List[str]

    flag_summary: List[FlagSummary]

    # feeds forward into next Setup Agent call as session_package.previous_session_report_summary
    narrative_summary: str
