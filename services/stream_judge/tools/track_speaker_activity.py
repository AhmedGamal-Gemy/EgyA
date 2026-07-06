"""Ghosting/disengagement detection — flagged in the plan as the shakiest
technical piece (diarization label instability). Falls back to overall
speaking-time balance if per-speaker tracking proves unreliable — see plan
section 6 and the Day-2 cut trigger in section 9.
"""

import time

from shared.constants import DISENGAGEMENT_SILENCE_THRESHOLD_SECONDS

_last_active: dict[str, float] = {}  # speaker_id -> last spoke timestamp


def track_speaker_activity(speaker_id: str, timestamp: float | None = None) -> None:
    _last_active[speaker_id] = timestamp or time.time()


def check_disengagement(known_speaker_ids: list[str]) -> list[str]:
    """Returns speaker_ids who've been silent past the threshold."""
    now = time.time()
    disengaged = []
    for speaker_id in known_speaker_ids:
        last_seen = _last_active.get(speaker_id)
        if last_seen is None or (now - last_seen) > DISENGAGEMENT_SILENCE_THRESHOLD_SECONDS:
            disengaged.append(speaker_id)
    return disengaged


# FALLBACK (if diarization proves unreliable — see plan section 9, open questions):
# drop per-identity tracking, use total speaking-time balance across detected
# speakers instead. Not implemented here yet — only build this out if the
# Day-1/2 diarization spike fails.
