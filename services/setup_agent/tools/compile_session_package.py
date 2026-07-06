"""See plan section 7.5 — Setup Agent tools.

Bundles the other four tools' output into one SessionPackage — this is the
direct hand-off to Stream Judge (expected answers for correctness-checking)
and to the frontend (what the instructor sees before the session starts).
"""

from shared.enums.flag_type import AudienceLevel
from shared.schemas.session_package import SessionPackage
from tools.generate_slides import generate_slides
from tools.generate_explanations import generate_explanations
from tools.generate_activities import generate_activities
from tools.generate_quiz import generate_quiz


async def compile_session_package(
    session_id: str,
    topic: str,
    audience_level: AudienceLevel,
    goals: list[str],
    previous_session_report_summary: str | None = None,
) -> SessionPackage:
    slides = await generate_slides(topic, audience_level, goals)
    explanations = await generate_explanations(topic, audience_level)
    activities = await generate_activities(topic, audience_level)
    quiz = await generate_quiz(topic, audience_level)

    return SessionPackage(
        session_id=session_id,
        topic=topic,
        audience_level=audience_level,
        goals=goals,
        slides=slides,
        explanations=explanations,
        activities=activities,
        quiz=quiz,
        previous_session_report_summary=previous_session_report_summary,
    )
