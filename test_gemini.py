import asyncio
import os
from google.adk.models.lite_llm import LiteLlm
from shared.schemas.flag import Flag
from shared.enums.flag_type import FlagType
from shared.schemas.report import FlagSummary
from services.report_agent.tools.generate_report import generate_report
from services.report_agent.agent import root_agent

# Bypass proxy for direct test to avoid port 4000 connection errors
root_agent.model = LiteLlm(
    model="gemini/gemini-2.5-flash", api_key=os.environ.get("GEMINI_API_KEY")
)


async def main():
    print("Running generate_report with Gemini directly...")
    session_id = "test_session_123"
    flags = []
    flag_summary = [
        FlagSummary(
            flag_type=FlagType.CONFUSION,
            count=2,
            examples=[
                "Ahmed asked for clarification",
                "Sondos was confused about pointers",
            ],
        )
    ]

    report = await generate_report(session_id, flags, flag_summary)
    print("\n--- GENERATED REPORT ---")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
