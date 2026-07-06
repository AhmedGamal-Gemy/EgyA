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
async def generate_report(session_id: str):
    # TODO: fetch_session_flags -> aggregate_flags -> generate_report (LLM call)
    # -> push_to_next_setup. See plan section 6, Post-Session Report Agent.
    raise NotImplementedError("Wire this up — see plan section 6")
