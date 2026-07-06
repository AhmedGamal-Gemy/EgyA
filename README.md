# AI Education Session Copilot

AMD Developer Hackathon: ACT II — Unicorn Track
Team: Ahmed Gamal, Sondos Mohammed

Full plan: see `AI-Education-Session-Copilot-Plan.md` (kept alongside this repo, not committed here unless you want it in-repo too).

## Quickstart

```bash
cp .env.example .env
# fill in FIREWORKS_API_KEY at minimum to get started

docker compose up --build
```

Services:
- `setup-agent` — :8001
- `stream-judge` — :8002
- `report-agent` — :8003
- `litellm-proxy` — :4000
- `whisper-livekit` — :8000
- `redis` — :6379

## Day 1 priority

Get `whisper-livekit` running and confirm you're receiving transcript chunks
over its `/asr` WebSocket before building anything downstream — see
`services/stream_judge/ws_client.py` and plan section 9.

## Status

Skeleton only — every tool function currently raises `NotImplementedError`
or is a stub. See inline `TODO`s and the plan doc for what goes where.
