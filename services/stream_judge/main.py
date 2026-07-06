from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from transcript_receiver import router as transcript_router

app = FastAPI(title="Stream Judge")

# The frontend runs on its own origin (different port) — without this,
# the browser's fetch() calls from app.js would be silently blocked by
# CORS. Wide open ("*") is fine for a hackathon demo, not for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcript_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "stream_judge"}
