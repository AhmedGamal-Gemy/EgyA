# Plan Clarifications & Enhancements

**Do not edit PLAN.md — this file lives alongside it as a companion.**

---

## 1. Development Workflow (not detailed in the plan)

The plan (section 5b) says "develop and experiment locally first, keep main clean, then pull onto AMD Cloud instance." It doesn't spell out the per-person workflow. Three approaches:

### Approach A — Local service, Docker infra

```bash
# Terminal 1: Infrastructure containers (start once, leave running)
docker compose up redis litellm-proxy -d

# Terminal 2: Your service with hot-reload
cd services/setup_agent
uv venv
uv pip install -e .
uv run uvicorn main:app --port 8001 --reload
```

Service restarts on every file save (`--reload`). Requires Python 3.11+ and uv installed locally.

### Approach B — All in Docker

```bash
docker compose up --build
```

Rebuilds and starts everything. Every code change needs a rebuild.

### Approach C — Per-person local service, shared Docker infra

```bash
# Infrastructure
docker compose up redis litellm-proxy -d

# Person A runs their service locally
uv run uvicorn services.setup_agent.main:app --port 8001 --reload

# Person B runs their service locally on a different port
uv run uvicorn services.stream_judge.main:app --port 8002 --reload
```

Both hit the same Redis + LiteLLM containers. Each gets hot-reload on their own code without rebuilding the other person's container.

---

## 2. Dockerfile: `uv pip install -r pyproject.toml` — RESOLVED

**Update (July 8):** This was tested and confirmed working — `uv pip install --system -r pyproject.toml` correctly installs from a properly-formatted pyproject.toml. The Dockerfiles are correct as-is (see PLAN.md section 8a for the full verification).

---

## 3. ⚠️ ASR Confidence Scores — WhisperLiveKit Doesn't Provide Them — RESOLVED

**Update (July 8):** The codebase now handles this correctly:
- `ASR_LOW_CONFIDENCE_THRESHOLD` constant removed from `shared/constants.py`
- `check_answer_correctness` uses the LLM's own three-way verdict (`correct`/`incorrect`/`uncertain`) with a prompt that explicitly instructs uncertainty on garbled/ambiguous transcripts — no numeric confidence pre-filter
- `UNCERTAIN_ANSWER` FlagType retained as the LLM's own judgment output (not a confidence gate), which is the correct pattern

---

## 4. Missing Pieces in the Skeleton

### `agent.py` files — RESOLVED

All three services have `agent.py` with working ADK agent definitions importing `LiteLlm` from `google.adk.models.lite_llm`. `shared/run_agent.py` exists and is ready.

### Setup Agent `tools/` — STILL STUBS

All 5 files exist: `generate_slides.py`, `generate_explanations.py`, `generate_activities.py`, `generate_quiz.py`, `compile_session_package.py` — but each raises `NotImplementedError`. No LLM calls wired yet. ADK agent also has `tools=[]` — tools not imported/wired.

### Stream Judge — tools RESOLVED

All 6 tools exist and are wired with real LLM calls:
- `check_answer_correctness.py` ✅ — Groq/LiteLLM call, three-way verdict, retry logic
- `assess_pacing_clarity.py` ✅ — Groq/LiteLLM call, JSON output parsing
- `detect_confusion.py` ✅ — Groq/LiteLLM call, yes/no verdict
- `notify_instructor.py` ✅ — WebSocket push to dashboard
- `track_speaker_activity.py` ✅ — in-memory per-speaker tracking
- `write_flag.py` ✅ — Redis-backed flag persistence

**Remaining:** `transcript_receiver.py` is still a stub — the orchestration endpoint that receives chunks from the frontend and calls the tools above is not wired.

### Report Agent — tools MOSTLY RESOLVED

All 4 files exist and are wired:
- `fetch_session_flags.py` ✅ — Redis read, returns typed Flag objects
- `aggregate_flags.py` ✅ — Groups/counts by flag_type
- `generate_report.py` ✅ — Groq/LiteLLM call, structured SessionReport output
- `push_to_next_setup.py` — Exists but calls Setup Agent endpoint that doesn't exist yet

### `prompts/` directories — RESOLVED (inline)

Empty `prompts/README.md` placeholders deleted. Prompts are now embedded directly in each tool's Python function, which is the better pattern — keeps prompt + tool call co-located.

---

## 5. `pyproject.toml` Missing `[build-system]` — RESOLVED

All three `pyproject.toml` files now have `[build-system]` tables. `uv pip install -e .` works correctly (verified in PLAN.md section 8a).

---

## 6. Owner Reference

| Service | Owner | Status |
|---|---|---|
| `services/setup_agent/` | Ahmed | 🟡 **Stub** — `POST /setup` raises NotImplementedError. All 5 tool files exist but are stubs. ADK agent `tools=[]`. Needs LLM calls wired + endpoint implemented. |
| `services/stream_judge/` | Sondos + Ahmed | 🟡 **Tools done, endpoint stub** — All 6 tools wired with real LLM calls (check_answer_correctness ✅, assess_pacing_clarity ✅, detect_confusion ✅, write_flag ✅, track_speaker_activity ✅, notify_instructor ✅). **`transcript_receiver.py` still a stub** — the orchestration endpoint that calls the tools when a chunk arrives is not wired. |
| `services/report_agent/` | Sondos | ✅ **Mostly done** — `POST /report` fully wired (fetch → aggregate → LLM generate → push). `push_to_next_setup` calls Setup Agent endpoint that doesn't exist yet (non-blocking for demo). |
| `shared/schemas/` | Both | ✅ Done — Flag, SessionPackage, SessionReport, FlagSummary |
| `shared/enums/` | Both | ✅ Done |
| `shared/run_agent.py` | Both | ✅ Ready |
| `shared/constants.py` | Both | ✅ Done |
| `shared/litellm_config.yaml` | Both | ✅ 5 model providers configured (Fireworks, Gemini, AMD Cloud, Ollama, Gemma) |
| `frontend/` | Sondos | ✅ Real end-to-end verified — audio flows to WhisperLiveKit, config.js + envsubst for port overrides |
| `docker-compose.yml` | Shared | ✅ All 7 services wired, parameterized ports, healthchecks |
