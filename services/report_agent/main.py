from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.schemas.report import SessionReport

app = FastAPI(title="Report Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "report_agent"}


@app.post("/session/{session_id}/report", response_model=SessionReport)
async def generate_report_endpoint(session_id: str):
    from services.report_agent.tools.fetch_session_flags import fetch_session_flags
    from services.report_agent.tools.aggregate_flags import aggregate_flags
    from services.report_agent.tools.generate_report import generate_report
    from services.report_agent.tools.push_to_next_setup import push_to_next_setup

    # 1. Fetch flags from redis
    try:
        flags = await fetch_session_flags(session_id)
    except Exception as e:
        print(
            f"Failed to fetch flags from Redis ({e}). Using empty list for dummy run."
        )
        flags = []

    # 2. Aggregate them
    summary = aggregate_flags(flags)

    # 3. Generate the report (LLM or fallback)
    report = await generate_report(session_id, flags, summary)

    # 4. Push to next setup
    try:
        await push_to_next_setup(report, f"next_{session_id}")
    except Exception as e:
        print(f"Failed to push to next setup ({e}). Ignoring for dummy run.")

    return report
