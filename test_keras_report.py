import asyncio
import os
import json

# Load .env manually for testing
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

from shared.enums.flag_type import FlagType
from shared.schemas.report import FlagSummary
from services.report_agent.tools.generate_report import generate_report

async def main():
    print("==================================================")
    print("Testing Report Agent with a simulated Keras Session (GROQ)")
    print("==================================================\n")
    session_id = "keras_session_001"

    flags = []

    # Simulate FlagSummaries extracted from the Keras transcript session
    flag_summary = [
        FlagSummary(
            flag_type=FlagType.CONFUSION,
            count=2,
            examples=[
                "Student 2: 'Wait a second, I am a bit lost here. Why do we put the (inputs) at the very end of the Dense layer line?'",
                "Student 1: 'I completely missed everything you just did with GradientTape.'"
            ],
        ),
        FlagSummary(
            flag_type=FlagType.WRONG_ANSWER,
            count=1,
            examples=[
                "Question: what is the default optimizer we usually use when compiling our Keras models for basic classification? Student 3 answered: 'I think it is the mean squared error optimizer.' (Expected: Adam optimizer)",
            ],
        ),
        FlagSummary(
            flag_type=FlagType.PACING,
            count=1,
            examples=[
                "System: Pacing check - explanation of GradientTape was very fast. Student 1 requested to slow down."
            ],
        ),
        FlagSummary(
            flag_type=FlagType.CLARITY,
            count=1,
            examples=[
                "System: Clarity check - Functional API syntax was unclear for Student 2."
            ],
        ),
        FlagSummary(
            flag_type=FlagType.DISENGAGEMENT,
            count=1,
            examples=[
                "Student 4 hasn't participated during the entire session."
            ],
        ),
    ]

    print("[Mocking the session data...]")
    for fs in flag_summary:
        print(f" - {fs.flag_type.value.upper()} ({fs.count}): {fs.examples[0]}")

    print("\nCalling Report Agent to generate the session summary...")

    report = await generate_report(session_id, flags, flag_summary)

    print("\n================ GENERATED SESSION REPORT ================\n")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
