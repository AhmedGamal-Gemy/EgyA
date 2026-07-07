import asyncio
import json
import uuid
from datetime import datetime, timezone

from shared.enums.flag_type import FlagType, FlagSeverity
from shared.schemas.flag import Flag
from services.report_agent.tools.generate_report import generate_report
from services.report_agent.tools.aggregate_flags import aggregate_flags
from shared.schemas.report import SessionReport


async def run_dumb_data_test():
    session_id = "test_session_123"

    # Create some dumb flags
    flags = [
        Flag(
            session_id=session_id,
            flag_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            flag_type=FlagType.CONFUSION,
            severity=FlagSeverity.INFO,
            message="A student expressed confusion: 'Wait, what is a pointer?'",
            speaker_id="speaker_1",
            transcript_chunk="Wait, what is a pointer?",
        ),
        Flag(
            session_id=session_id,
            flag_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            flag_type=FlagType.WRONG_ANSWER,
            severity=FlagSeverity.INFO,
            message="Student answered incorrectly on: 'What is a pointer?' (expected: memory address)",
            speaker_id="speaker_2",
            question="What is a pointer?",
            expected_answer="memory address",
            student_utterance="A dog",
            transcript_chunk="A dog",
        ),
        Flag(
            session_id=session_id,
            flag_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            flag_type=FlagType.DISENGAGEMENT,
            severity=FlagSeverity.WARNING,
            message="speaker_3 hasn't participated in a while — consider checking in with them.",
            speaker_id="speaker_3",
        ),
        Flag(
            session_id=session_id,
            flag_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            flag_type=FlagType.PACING,
            severity=FlagSeverity.WARNING,
            message="Pacing check: this section is running fast for a kids audience — consider adjusting speed.",
        ),
    ]

    print("Created dumb flags:")
    for f in flags:
        print(f" - {f.flag_type}: {f.message}")

    print("\nAggregating flags...")
    summary = aggregate_flags(flags)

    print("\nGenerating report...")
    report: SessionReport = await generate_report(session_id, flags, summary)

    print("\n--- FINAL DUMB REPORT ---")
    print(json.dumps(report.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(run_dumb_data_test())
