from enum import Enum


class FlagType(str, Enum):
    PACING = "pacing"                      # teacher-side
    CLARITY = "clarity"                    # teacher-side
    CONFUSION = "confusion"                # student-side
    WRONG_ANSWER = "wrong_answer"          # student-side
    UNCERTAIN_ANSWER = "uncertain_answer"  # student-side, low ASR confidence — don't force a verdict
    DISENGAGEMENT = "disengagement"        # student-side, ghosting/participation gap


class FlagSeverity(str, Enum):
    INFO = "info"        # worth noting in the report, not urgent live
    WARNING = "warning"  # worth a live nudge to the instructor


class AudienceLevel(str, Enum):
    KIDS = "kids"
    YOUTH = "youth"
    ADULTS = "adults"


# Templates keyed by FlagType — filled in with the flag's specific details.
# Decision: message is templated, not LLM-generated per flag (see plan section 6a) —
# faster, cheaper, and more predictable under hackathon time pressure. Save LLM-generated
# prose for the Report Agent's final narrative, not every real-time flag.
FLAG_MESSAGE_TEMPLATES: dict[FlagType, str] = {
    FlagType.PACING: "Pacing check: this section is running {detail} for a {audience_level} audience — consider adjusting speed.",
    FlagType.CLARITY: "Clarity check: the explanation style here may not match a {audience_level} audience — consider re-explaining with simpler terms.",
    FlagType.CONFUSION: 'A student expressed confusion: "{detail}"',
    FlagType.WRONG_ANSWER: 'Student answered incorrectly on: "{question}" (expected: {expected_answer})',
    FlagType.UNCERTAIN_ANSWER: 'Couldn\'t confidently judge a student\'s answer to "{question}" — audio was unclear, consider asking them to repeat it.',
    FlagType.DISENGAGEMENT: "{speaker_id} hasn't participated in a while — consider checking in with them.",
}


def render_flag_message(flag_type: FlagType, **kwargs) -> str:
    """Fill in the template for a given flag type with the provided details.

    Any placeholder not supplied in kwargs is left as-is rather than raising,
    so a missing detail doesn't crash flag creation mid-session.
    """
    template = FLAG_MESSAGE_TEMPLATES[flag_type]
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
