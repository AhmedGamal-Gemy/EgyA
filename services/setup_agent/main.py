from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.enums.flag_type import AudienceLevel
from shared.schemas.session_package import SessionPackage

app = FastAPI(title="Setup Agent")

# See stream_judge/main.py for why this is needed — same cross-origin
# frontend calling in.
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
    # TODO: wire to shared/run_agent.py + tools/compile_session_package.py
    raise NotImplementedError("Wire this up on Day 1 — see plan section 6, Setup Agent")
