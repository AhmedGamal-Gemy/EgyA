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

## 2. Dockerfile: `uv pip install -r pyproject.toml` Won't Work

Every service Dockerfile contains:

```dockerfile
COPY services/X/pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml
```

`-r` flag reads requirements.txt format (`package>=version` per line). `pyproject.toml` is TOML — parsers will reject it.

---

## 3. ⚠️ ASR Confidence Scores — WhisperLiveKit Doesn't Provide Them

The plan (section 6) references `ASR_LOW_CONFIDENCE_THRESHOLD = 0.6` and `asr_confidence` to gate compounding errors. The `check_answer_correctness` function returns `"uncertain"` when confidence is below that threshold.

**WhisperLiveKit's actual behavior:**

| Endpoint | Confidence output |
|---|---|
| Native `/asr` WebSocket | None — `FrontData` schema has `text`, `speaker`, timestamps but no confidence field |
| Deepgram-compat `/v1/listen` | Hardcoded to `0.0` — confirmed in source (`whisperlivekit/deepgram_compat.py` lines 66 and 112) |

**Consequence:** If the `ASR_LOW_CONFIDENCE_THRESHOLD` gate is enforced, `check_answer_correctness` will always receive 0.0 (or undefined) and always return `"uncertain"`. Correctness checking will be non-functional with the gate in place.

The `ASR_LOW_CONFIDENCE_THRESHOLD` constant, `UNCERTAIN_ANSWER` FlagType, and `check_answer_correctness`'s confidence gate all depend on confidence data that WhisperLiveKit does not currently emit.

---

## 4. Missing Pieces in the Skeleton

### `agent.py` files

The plan (section 8) shows `services/*/agent.py` for each service (ADK agent definitions). None exist. `shared/run_agent.py` exists and is ready, but nothing imports it.

### Setup Agent `tools/` — empty

Plan lists: `generate_slides.py`, `generate_explanations.py`, `generate_activities.py`, `generate_quiz.py`, `compile_session_package.py`. None exist.

### Stream Judge — missing tools

Plan lists: `assess_pacing_clarity.py`, `detect_confusion.py`, `notify_instructor.py`. None exist. `check_answer_correctness.py` exists but has no LLM call wired. `track_speaker_activity.py` and `write_flag.py` are implemented.

### Report Agent — missing tools

Plan lists: `generate_report.py`, `push_to_next_setup.py`. None exist. `fetch_session_flags.py` and `aggregate_flags.py` are implemented.

### `prompts/` directories — all empty

All three services have `prompts/` directories. All are empty.

---

## 5. `pyproject.toml` Missing `[build-system]`

Each service's `pyproject.toml` has `[project]` with dependencies listed, but no `[build-system]` table. `pip install -e .` may not work without it.

---

## 6. Owner Reference

| Service | Owner | Status |
|---|---|---|
| `services/setup_agent/` | Ahmed | Stub — `POST /setup` raises NotImplementedError, tools/ empty |
| `services/stream_judge/` | Sondos + Ahmed | `POST /transcript-chunk` stub, 3/6 tools exist (write_flag ✅, track_speaker_activity ✅, check_answer_correctness ❌) |
| `services/report_agent/` | Sondos | `POST /report` raises NotImplementedError, 2/4 tools exist (fetch_session_flags ✅, aggregate_flags ✅) |
| `shared/schemas/` | Both | Flag, SessionPackage, SessionReport ✅ |
| `shared/enums/` | Both | FlagType, FlagSeverity, AudienceLevel, message templates ✅ |
| `shared/run_agent.py` | Both | Ready ✅ |
| `shared/constants.py` | Both | `ASR_LOW_CONFIDENCE_THRESHOLD` — see section 3 |
| `frontend/` | Sondos | Capture pipeline scaffolded ✅ — parseTranscriptMessage() needs real server verification |
| `docker-compose.yml` | Shared | All 6 services wired ✅ — see section 2 for Dockerfile build issue |
