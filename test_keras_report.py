import asyncio
import os
from google.adk.models.lite_llm import LiteLlm
from shared.enums.flag_type import FlagType
from shared.schemas.report import FlagSummary
from services.report_agent.tools.generate_report import generate_report
from services.report_agent.agent import root_agent

# Use Gemini directly
root_agent.model = LiteLlm(
    model="gemini/gemini-2.5-flash", api_key=os.environ.get("GEMINI_API_KEY")
)


async def main():
    print("Testing Report Agent with a simulated Keras Session...")
    session_id = "keras_session_001"

    # We pass empty flags because the current generate_report prompt
    # only reads from flag_summary.
    flags = []

    # Simulate FlagSummaries extracted from the Keras transcript session
    flag_summary = [
        FlagSummary(
            flag_type=FlagType.CONFUSION,
            count=1,
            examples=[
                "Student 1: 'Wait, why do we need multiple inputs? I don't get the Siamese network example.'"
            ],
        ),
        FlagSummary(
            flag_type=FlagType.WRONG_ANSWER,
            count=2,
            examples=[
                "Question: Which API offers the most flexibility? Student 1 answered: 'Sequential API' (Expected: Subclassing API)",
                "Question: What does tf.GradientTape do? Student 2 answered: 'It stacks layers' (Expected: Custom training loop)",
            ],
        ),
        FlagSummary(
            flag_type=FlagType.PACING,
            count=1,
            examples=[
                "System: Pacing check - explanation of subclassing and dynamic graphs was very fast. Consider slowing down."
            ],
        ),
        FlagSummary(
            flag_type=FlagType.DISENGAGEMENT,
            count=1,
            examples=[
                "Student 3 hasn't participated during the entire subclassing section."
            ],
        ),
    ]

    print("\n[Mocking the session data...]")
    for fs in flag_summary:
        print(f" - {fs.flag_type.value.upper()} ({fs.count}): {fs.examples[0]}")

    print("\nCalling Report Agent to generate the session summary...")

    report = await generate_report(session_id, flags, flag_summary)

    print("\n================ GENERATED SESSION REPORT ================\n")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
