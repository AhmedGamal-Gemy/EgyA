from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.enums.flag_type import AudienceLevel
from shared.schemas.report import SessionReport
from shared.schemas.session_package import SessionPackage

app = FastAPI(title="Setup Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SetupRequest(BaseModel):
    session_id: str
    topic: str
    audience_level: AudienceLevel
    goals: list[str]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "setup_agent"}


@app.post("/setup", response_model=SessionPackage)
async def setup(req: SetupRequest):
    from tools.compile_session_package import compile_session_package
    return await compile_session_package(
        session_id=req.session_id,
        topic=req.topic,
        audience_level=req.audience_level,
        goals=req.goals,
    )


@app.post("/session/{session_id}/previous-report")
async def receive_previous_report(session_id: str, report: SessionReport):
    print(f"[setup_agent] Received previous report for session {session_id}")
    return {"status": "ok", "session_id": session_id}
