"""Receives confirmed transcript lines forwarded from the browser.

Architecture note (see plan section 6): the browser connects DIRECTLY to
WhisperLiveKit's /asr WebSocket (Option A) — each WhisperLiveKit connection
is its own independent transcription session, so the browser can reuse
WhisperLiveKit's own protocol (mode=diff) for mic/tab capture and line
reconstruction. WhisperLiveKit sends transcript results back to the
browser; the browser then forwards each newly-committed line here.

CORRECTION vs an earlier draft: this no longer expects a `confidence`
field on incoming chunks. Confirmed via WhisperLiveKit's own docs/API.md
and Deepgram-compat source that no real per-line confidence score is
provided anywhere in the protocol — see shared/constants.py and
tools/check_answer_correctness.py for the full explanation. Uncertainty
is now handled by the Judge LLM's own three-way verdict instead.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TranscriptChunk(BaseModel):
    session_id: str
    text: str
    speaker_id: str | None = None


@router.post("/session/{session_id}/transcript-chunk")
async def receive_transcript_chunk(session_id: str, chunk: TranscriptChunk):
    """Called by the browser once per newly-committed WhisperLiveKit line
    (see plan section 6, batching strategy)."""

    # TODO Day 2: track_speaker_activity, assess_pacing_clarity, detect_confusion,
    # check_answer_correctness (if this chunk answers a pending quiz question),
    # then write_flag for whatever fires. See plan section 6/6a.
    raise NotImplementedError("Wire up the judgment pipeline — see plan section 6, Stream Judge")
