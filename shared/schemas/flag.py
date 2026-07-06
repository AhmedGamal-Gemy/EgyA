import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from shared.enums.flag_type import FlagType, FlagSeverity, render_flag_message


class Flag(BaseModel):
    # identity / routing
    session_id: str
    flag_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # what happened
    flag_type: FlagType
    severity: FlagSeverity = FlagSeverity.INFO
    message: str  # rendered from FLAG_MESSAGE_TEMPLATES[flag_type], not LLM-generated per flag

    # who it's about (student-side flags only; None for teacher-side)
    speaker_id: Optional[str] = None  # diarization label, e.g. "speaker_2"

    # correctness-specific fields (only populated for WRONG_ANSWER / UNCERTAIN_ANSWER)
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    student_utterance: Optional[str] = None
    # NOTE: an asr_confidence field used to live here. Removed — confirmed
    # WhisperLiveKit provides no real per-line confidence score anywhere in
    # its protocol (native /asr has none; Deepgram-compat hardcodes 0.0).
    # UNCERTAIN_ANSWER is now driven entirely by the Judge LLM's own verdict,
    # not a numeric field. See shared/constants.py and
    # services/stream_judge/tools/check_answer_correctness.py.

    # raw source, for debugging / report drill-down
    transcript_chunk: Optional[str] = None

    @classmethod
    def create(cls, session_id: str, flag_type: FlagType, **details) -> "Flag":
        """Convenience constructor: renders the templated message from flag_type
        and whatever details are passed, so callers don't have to import the
        template renderer separately every time.
        """
        message = render_flag_message(flag_type, **details)
        known_fields = {
            k: v
            for k, v in details.items()
            if k
            in {
                "severity",
                "speaker_id",
                "question",
                "expected_answer",
                "student_utterance",
                "transcript_chunk",
            }
        }
        return cls(session_id=session_id, flag_type=flag_type, message=message, **known_fields)
