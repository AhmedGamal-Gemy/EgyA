# AI Education Session Copilot
### AMD Developer Hackathon: ACT II — Unicorn Track
**Team:** Ahmed Gamal, Sondos Mohammed | **Window:** July 6–11, 2026 (submit by 15:00 UTC July 11)

---

## 1. Positioning

**Not a content generator. Not a post-hoc grading tool.** A live copilot that watches a teaching session unfold (via audio) and coaches the instructor in real time on both sides of the room — flagging teacher-side pacing/clarity issues *and* student-side signals (confusion, wrong answers, disengagement, students going silent/ghosting the session) — then closes the loop with structured post-session insight that improves the *next* session.

**Why this wins on Unicorn judging criteria** (creativity, originality, completeness, AMD platform usage, product/market potential):
- **Originality:** existing tools (Observation Copilot, Sibme AI) are post-hoc only. Real-time systems that exist (Tutor CoPilot) are 1:1 tutoring, on-demand pull, not classroom, not proactive push. ClassAid is real-time but scoped to programming-activity orchestration, not general audio-based coaching. Nobody combines live bidirectional coaching (teacher-side + student-side) with a closed feedback loop into next-session generation.
- **Market potential:** direct pipeline into Ahmed's own internship program (10-11 students, July 15 launch) as a live use case/testimonial. Broader market: any tutoring org, bootcamp, or NGO teaching program (e.g., Resala's own education tracks).
- **Completeness:** three distinct agent roles, each independently demoable, tied together by one shared state layer (Redis) — judges can see a full loop (setup → live session → report → next setup) not just one flashy piece.

---

## 2. Locked MVP Scope

| Component | In scope for hackathon | Explicitly OUT (roadmap) |
|---|---|---|
| Setup Agent | Topic/level/goals → slides, explanations, activities, quiz via LLM | Custom slide design/animation, multi-format export |
| Stream Judge | Live local audio → WhisperLiveKit transcription → LLM judgment (teacher pacing/clarity + student correctness/engagement/ghosting) → live flag to instructor | Video input, multi-room/multi-mic support, real emotion detection from voice tone |
| Post-Session Report | Aggregate flags → structured report → feeds next Setup Agent call | Longitudinal cross-session trend analytics, multi-instructor comparison |

**Non-negotiable before demo:** the loop must run end-to-end once, live, on a real (even if short, staged) teaching segment — that's your completeness proof.

---

## 3. Tech Stack

| Layer | Tool | Rationale |
|---|---|---|
| LLM gateway | **LiteLLM Proxy** | Single interface across Fireworks AI and AMD Developer Cloud-hosted models (Qwen, Llama, DeepSeek, Mistral) — swap by config, not code. Also enables local Ollama fallback if credits run low. |
| Agent orchestration | **Google ADK** (standard agents, *not* Bidi-streaming), shared Runner helper | Write one small helper (`shared/run_agent.py`, ~15 lines: `Runner` + `InMemorySessionService` + `Content` wrapping) once, reuse across all three agents — considered and rejected exposing agents via A2A (`to_a2a()`) instead: A2A's real value is cross-team/cross-language/cross-vendor interoperability, which doesn't apply here (same team, same framework, same repo), and it introduces real overhead (security/auth surface, a recently-patched `context_id`↔session mapping bug in `adk-python`) for a problem you don't have. Bidi-streaming (`LiveRequestQueue`/`run_live()`) is a separate, unrelated ADK feature built around the Gemini Live API's native audio understanding — not used, since it would lock you to Gemini Live models and conflict with the LiteLLM-agnostic design. |
| Live transcription + diarization + streaming policy | **WhisperLiveKit**, using the **LocalAgreement** policy (not SimulStreaming) | Wraps faster-whisper, LocalAgreement *and* SimulStreaming policies, and pyannote/Sortformer-based diarization in one maintained repo. WebSocket (`/asr`) + OpenAI-compatible REST + Deepgram-compatible WebSocket. **Policy choice:** LocalAgreement trades slightly higher latency for stability and is WhisperLiveKit's default for most users, with the original research reporting ~3.3s latency and demonstrated robustness in a live multilingual-conference deployment. SimulStreaming is faster (~5x) and was best-performing in IWSLT 2025, but only supports a torch backend and has had recent bug fixes (VRAM leaks, crashes) in its last few releases — too risky for a live hackathon demo where a crash mid-session is worse than a few extra seconds of latency. **⚠️ AMD GPU risk — see section 5b:** WhisperLiveKit's GPU path runs on faster-whisper → CTranslate2, and upstream CTranslate2 has no ROCm backend (NVIDIA CUDA + CPU only, no ROCm wheels on PyPI). Treat CPU-only ASR as the working assumption, not GPU-on-AMD-Cloud. |
| Backend | **FastAPI** per service | Matches your existing Vexel/Inspect pattern |
| State/session store | **Redis** (raw `redis-py` client, wrapped in typed functions) | Shared between Stream Judge (writes flags in real time) and Report Agent (reads at session end). **Reconsidered from an earlier draft that added `redis/mcp-redis`** — that choice contradicted the same reasoning used to reject A2A: it's an extra containerized service, auth surface, and dependency for a single internal Redis instance both agents already have direct access to. A raw `redis-py` client behind the same typed `write_flag`/`fetch_session_flags` wrapper functions gives identical schema enforcement (via the `Flag` Pydantic model + function signature, not MCP) with one less service to debug on Day 4. |
| Frontend | React, or a minimal Gradio/plain HTML+JS UI (WhisperLiveKit ships one you can adapt) | Setup form, live instructor dashboard (private flag stream), post-session report view — owned by Ahmed/Sondos given no dedicated frontend teammate |
| Logging | Loguru | Structured logs across services, consistent with your usual stack |
| Package mgmt | `uv` | Faster, matches your other projects |

**Fireworks ↔ AMD Developer Cloud:** both are LiteLLM providers — config-only swap. Use Fireworks for fast hosted inference during early dev (gloss/report generation calls), switch to AMD Developer Cloud-hosted models if you want to demonstrate actual AMD GPU usage for judging (worth doing for at least one agent, since "use of AMD platforms" is an explicit judging criterion).

**Bonus, low-cost opportunity — "Best Use of Gemma Models" side challenge:** Gemma is a confirmed tech partner for this hackathon, accessible via both Fireworks AI and AMD Developer Cloud with no separate sign-up, drawn from existing hackathon/ADP credits. Since every agent already calls through LiteLLM with a swappable model alias, pointing **one** agent's calls (e.g. Report Agent's summary generation) at a Gemma model is a one-line config change — near-zero extra effort for a shot at an additional prize category alongside the Unicorn track submission.

---

## 4. System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Ahmed/Sondos), Chrome/Edge only          │
│   Setup Form · Live Instructor Dashboard · Report View                │
│   getDisplayMedia() tab-audio capture → AudioWorklet → 16kHz PCM       │
└───┬───────────────────────┬───────────────────────┬───────────────────┘
    │ REST                  │ WebSocket, direct       │ WebSocket, forwards
    │                        │ (audio out,             │ each confirmed
    │                        │  transcript in)         │ transcript chunk
    ▼                        ▼                         ▼
┌───────────────┐   ┌─────────────────────┐   ┌─────────────────────────┐
│ Setup Agent     │   │  WhisperLiveKit      │   │   Stream Judge            │
│ (Ahmed)         │   │  (own container)     │   │   (Sondos + Ahmed)        │
│ FastAPI + ADK   │   │  --pcm-input,         │   │                           │
│ (shared Runner  │   │  --backend whisper,   │──▶│  ADK Judge Agent          │
│  helper)        │   │  --backend-policy     │   │  (shared Runner helper)   │
│ in: topic/level │   │  localagreement,      │   │  via LiteLLM proxy         │
│ /goals          │   │  --diarization        │   │  → pacing/clarity (teacher)│
│ out: slides/    │   └───────────────────────┘   │  → confusion/engagement    │
│ quiz/games      │                                │    (student)               │
│ via LiteLLM      │                                └─────────────┬─────────────┘
└───────┬─────────┘                                               │ flagged event
        │                                                          ▼
        │                                              Redis (session flags,
        │                                              live + persisted log)
        │                                                          │ full session flag log
        ▼                                                          ▼
      ┌─────────────────────────────────────────────────┐
      │   Post-Session Report Agent (Sondos)                │
      │   (via shared Runner helper)                          │
      │   aggregate flags → structured report                │
      │   → feeds forward into next Setup Agent call          │
      │     (plain HTTP call from Report Agent's FastAPI        │
      │      service to Setup Agent's endpoint)                 │
      └─────────────────────────────────────────────────┘

      ┌─────────────────────────────────────────────────┐
      │   litellm-proxy (shared service, all 3 agents)      │
      │   Fireworks AI  ⇄  AMD Developer Cloud  ⇄  Ollama     │
      └─────────────────────────────────────────────────┘
```

**Design decision to confirm with Sondos:** the live notifier (instructor dashboard) and the end-of-session aggregator should read from the *same* Redis flag schema, so Stream Judge and Report Agent don't drift into two different data shapes. Lock this schema on Day 1 before either piece is built.

**Considered and rejected: wiring all three agents via the A2A protocol** (`to_a2a()`/`RemoteA2aAgent`), to eliminate ADK Runner boilerplate. Verdict after research: A2A's real value is cross-team/cross-language/cross-vendor agent interoperability (Google's own examples are things like a Python agent built by one team calling a Go agent built by another) — not applicable here, since both of you are building all three agents in the same language, framework, and repo. It also introduces real overhead (auth/security surface, and a recently-patched bug in `adk-python` around mapping A2A `context_id` to ADK sessions) for a problem this project doesn't have. Sticking with a shared Runner helper function instead — same modularity (separate containers, independently testable), none of the added protocol surface.

---

## 5. Docker Images / Services

| Service | Image source | Notes |
|---|---|---|
| `whisper-livekit` | Official `Dockerfile.cpu` from QuentinFuxa/WhisperLiveKit (CPU is the working assumption — see section 5b for the AMD GPU risk) | Only attempt the GPU profile as a stretch goal if a Day-0 spike confirms it works on AMD Developer Cloud specifically |
| `setup-agent` | Custom, FastAPI + ADK, Dockerfile from scratch | Lightweight — no GPU needed, pure LLM calls |
| `stream-judge` | Custom, FastAPI + ADK judge agent, consumes WhisperLiveKit's WebSocket | Also lightweight — no GPU needed here, GPU load (if any) lives in whisper-livekit |
| `report-agent` | Custom, FastAPI + ADK | Lightweight |
| `litellm-proxy` | Official `ghcr.io/berriai/litellm` image, custom `config.yaml` mounted | Single shared gateway |
| `redis` | Official `redis:7-alpine` | Shared state, accessed via raw `redis-py` from Stream Judge and Report Agent |
| `frontend` | Node/Vite build, own Dockerfile | See section 7 — ownership rebalanced given load imbalance risk |

All services in one `docker-compose.yml` at repo root — this is your "containerized" submission requirement satisfied directly.

---

## 5b. Risk: WhisperLiveKit's GPU Path Likely Won't Run on AMD Hardware

**The problem:** WhisperLiveKit's GPU acceleration for faster-whisper depends on CTranslate2, and **upstream CTranslate2 has no ROCm backend** — it supports NVIDIA CUDA and CPU only, with no ROCm wheels published on PyPI. This is confirmed by multiple independent sources, including a direct account of someone hitting this exact wall trying to run faster-whisper on an AMD GPU. WhisperLiveKit's official Docker images are built for CUDA or CPU (`Dockerfile` / `Dockerfile.cpu`) — there is no official ROCm image.

**It's not just slower, it can be broken.** Community ROCm forks of CTranslate2 exist (e.g. `arlo-phoenix/CTranslate2-rocm`, prebuilt images like `pigeekcom/wyoming-faster-whisper-rocm`), but even these have open, reproducible crash reports on some AMD GPU architectures — a recent GitHub issue documents faster-whisper crashing with a GPU memory access fault on an AMD RX 9070 XT (gfx1201) across multiple model/precision settings. These community forks also target consumer/prosumer GPU architectures (gfx1100–gfx1151); it's unconfirmed whether any support the MI300X-class (gfx942) hardware AMD Developer Cloud actually provisions for this hackathon.

**What this changes about the plan:**
- **Treat CPU-only ASR, using `--backend whisper` (not the default `faster-whisper`), as the safe working assumption** — not a fallback bolted on after a failed attempt. Using the same backend on CPU as you'd use on AMD GPU (see next bullet) means no behavior changes when/if you switch hardware — one less variable to debug mid-hackathon.
- **A more promising path exists, and it's now reasonably confirmed rather than just plausible:** WhisperLiveKit ships a **vanilla PyTorch backend** (`--backend whisper`), completely separate from the CTranslate2-based `faster-whisper` default. Since PyTorch has official ROCm wheels, running with `--backend whisper` on a ROCm-enabled PyTorch install sidesteps the CTranslate2/ROCm problem entirely. **AMD's own official ROCm blog demonstrates exactly this** — running the same underlying `openai-whisper` package (which is what `--backend whisper` uses) directly on **MI210/MI250 GPUs**, with confirmed-correct transcription output. That's the GPU family AMD Developer Cloud most likely provisions, tested by AMD itself — not a community hack. This pattern holds up broadly: independent reports confirm vanilla PyTorch Whisper working on ROCm across a wide range of AMD GPUs, while `faster-whisper`/CTranslate2 consistently shows up as the one that's broken or crash-prone. **Plan to use `--backend whisper` directly rather than treating it as a long-shot spike** — it's expected to work, though still confirm it on the actual AMD Developer Cloud instance once provisioned, since the exact GPU model (MI210/MI250 vs newer MI300X) isn't guaranteed and diarization (Sortformer/Diart) is a separate PyTorch component that needs its own check even if base ASR works cleanly.
- **This also softens, but doesn't eliminate, the AMD-platform-usage concern.** With `--backend whisper` reasonably confirmed to work on AMD GPUs, GPU-accelerated ASR is a realistic part of your AMD platform story, not just a stretch goal — but don't make it the *only* claim either. **Keep the LLM inference layer** (Setup/Judge/Report agent calls routed through AMD Developer Cloud via the `LLM_PROVIDER` toggle in section 5a) **as your primary, guaranteed AMD usage claim**, with GPU-accelerated ASR as a strong secondary point once confirmed on the actual instance.
- **Agreed team workflow (from the July 6 kickoff meeting), and it's the right shape for this exact risk:** develop and experiment locally first (on whatever CPU/GPU either of you has), keep `main` clean via reviewed commits, then pull `main` onto the actual AMD Developer Cloud instance to test there. This correctly isolates "does the code work" (local, fast iteration) from "does it work on *this* specific hardware" (cloud instance, tested deliberately, not assumed). **Verify `--backend whisper` on the cloud instance once credits land (Day 2-3 at the earliest — see section 9's fallback trigger)** — confidence is high based on AMD's own published results, but still confirm on your actual provisioned GPU rather than assuming, since MI300X-class hardware specifically hasn't been directly confirmed in what's been found (MI210/MI250 has).
- **Day-0 spike, separate from "get WhisperLiveKit running locally":** testing WhisperLiveKit on your own laptop tells you nothing about the AMD Cloud instance specifically. Keep these as two explicitly separate checks: (1) local — does the pipeline logic work at all, any hardware; (2) cloud instance, once provisioned — confirm `--backend whisper` runs correctly on AMD's GPUs, matching AMD's own demonstrated pattern; if it doesn't for some reason, CPU-only ASR with AMD usage proven at the LLM layer is still a complete, defensible fallback.

---

## 5a. Environment & Config — Single Shared `.env`

**Important distinction to keep straight:** Docker Compose auto-loads a root `.env` file, but only for interpolating values *inside* `docker-compose.yml` itself (e.g. `${SOME_VAR}` in the YAML) — it does **not** automatically inject those variables into containers. To get variables into a container, each service needs an `env_file:` directive (or `environment:`) pointing at the file. The useful part: `env_file` can point to the **same shared root `.env`** from every service block, which is exactly the "one file, all services read from it" pattern — fully supported, common pattern, not a hack.

```
ai-session-copilot/
├── docker-compose.yml
├── .env                    # shared root file, gitignored
├── .env.example            # committed template, no real secrets
```

```yaml
# docker-compose.yml
services:
  setup-agent:
    env_file: [.env]
  stream-judge:
    env_file: [.env]
  report-agent:
    env_file: [.env]
  litellm-proxy:
    env_file: [.env]
```

```
# .env
LOG_LEVEL=info
LLM_PROVIDER=fireworks        # single toggle: swap to "amd_cloud" or "ollama" — every agent's LiteLLM call reads this
FIREWORKS_API_KEY=...
AMD_DEVELOPER_CLOUD_API_KEY=...
ASR_POLICY=localagreement     # vs simulstreaming — see section 3 rationale
BATCH_STRATEGY=vad_pause      # vs fixed_window — see section 6, Stream Judge
REDIS_URL=redis://redis:6379
```

**One documented caveat:** a single blanket `.env` means every service technically sees every variable, even ones it doesn't use (e.g. Setup Agent sees `ASR_POLICY` despite never touching WhisperLiveKit). This is a known tradeoff — cleaner setups scope variables per service — but for a 2-person, 5-day build the extra structure isn't worth the time; it's harmless noise, not a real risk.

**Why `LLM_PROVIDER` as a single shared toggle matters for you specifically:** flipping one value routes every agent's inference through AMD Developer Cloud instead of Fireworks — this is your lever for proving real AMD platform usage for judging (section 3/10), without touching code in three different services.

---

## 6. Agent Breakdown (ADK)

**1. Setup Agent**
- Input: topic, audience level, session goals
- Tool calls: `generate_slides`, `generate_explanations`, `generate_activities`, `generate_quiz` — each a LiteLLM call with level-tailored prompting
- Output: structured JSON bundle consumed by frontend before session start

**2. Stream Judge Agent**

**Audio capture — how the audio actually gets in (this was an open question, now resolved):** these are virtual/online classes over Zoom, Meet, or Teams, which changes the capture problem. Plain microphone capture (`getUserMedia()`) only gets the instructor's own voice — student audio arrives through the computer's *speakers* (from the call), not the mic, so mic-only capture would completely miss student responses, confusion, and participation. What's actually needed is **display/tab audio capture** (`getDisplayMedia({ video: true, audio: true })`), the same API behind the "choose what to share" picker in Meet/Zoom/Teams themselves.

- **Required flow:** instructor opens the dashboard in one Chrome tab, opens the meeting in **another Chrome tab running the platform's web client** (Zoom Web Client, Google Meet, or Microsoft Teams for web — not the native desktop app), then the dashboard calls `getDisplayMedia({ video: true, audio: true })`. The browser's native picker appears; instructor selects **"Chrome Tab"**, picks the meeting tab, and checks **"Share tab audio."**
- **Why not the native desktop apps:** native apps aren't browser tabs, so capturing their audio would require window/screen-level system-audio capture instead of tab-audio capture — meaningfully less reliable, especially on macOS, where system/window audio capture via this API has historically not been supported at all.
- **Explicit MVP scope constraint, stated plainly rather than silently assumed:** this flow is reliable on **Chrome/Edge only**. Safari and Firefox have inconsistent or absent tab-audio support. State this as a known constraint in the submission, not a hidden gap.
- **Downstream pipeline, once you have the `MediaStream`:** Web Audio API → `AudioWorklet` → downsample to **16kHz, 16-bit PCM (s16le)** — browsers default to 44.1/48kHz, so this downsampling step is required, not optional — then stream to WhisperLiveKit's `/asr` WebSocket, started with `--pcm-input` to skip its ffmpeg conversion path entirely.
- **Architecture decision — browser connects directly to WhisperLiveKit, not through Stream Judge's backend (Option A, chosen over relaying audio through Stream Judge):** each WhisperLiveKit WebSocket connection is its own independent transcription session, so the browser can use WhisperLiveKit's own shipped reference frontend (`whisperlivekit/web/live_transcription.html`) as a starting point — mic/tab capture, downsampling, and WebSocket handling are already solved there, adapting it is far less work than having Stream Judge relay two live audio streams itself. The browser receives transcript results back over that same connection, then **forwards each confirmed chunk to Stream Judge's own endpoint** (a small addition, not a full relay) for judgment, flagging, and everything downstream already designed below.

- Input: confirmed transcript chunk (forwarded from the browser, which received it from WhisperLiveKit) + diarized speaker labels + session context from Setup Agent (quiz questions/expected answers, activity prompts)
- **Batching strategy — how much confirmed text to collect before calling the Judge LLM:** WhisperLiveKit doesn't emit fixed-size chunks; it commits tokens incrementally as LocalAgreement stabilizes across consecutive re-transcriptions. Calling the LLM on every single confirmed word would be noisy and wasteful. **Decision: batch on VAD-detected pause**, not a fixed timer — WhisperLiveKit already runs Silero VAD internally for its own processing, so piggyback on that same silence signal to know when a speaker has finished a complete thought. This aligns naturally with when correctness-checking and confusion-detection actually have a complete, judgeable utterance, rather than a mid-sentence fragment.
- Three analysis passes (can be sub-agents or one LLM call with a structured multi-field schema):
  - **Teacher-side:** pacing, clarity, whether explanation style matches audience level
  - **Student-side — correctness & engagement:** when a student responds to a question/activity, compare their spoken answer (via transcript) against the expected answer from the Setup Agent's quiz/activity data; flag wrong answers and confusion signals from what students say/ask
  - **Student-side — participation/ghosting:** track per-speaker activity using diarization output. If a known participant (by speaker label) hasn't spoken for a configurable window despite prompts directed at the group, or stays silent through multiple activity check-ins, flag as a possible disengagement/"ghosting" signal
- Output: structured flag written to Redis + pushed to instructor dashboard privately — flag types: `pacing`, `clarity`, `wrong_answer`, `confusion`, `disengagement`
- **Note:** correctness checking requires Stream Judge to have read access to the Setup Agent's generated quiz/activity content (expected answers) — this is a direct dependency between the two agents, not just a shared Redis flag schema. Pass this context at session start (Setup Agent's output → Stream Judge's session config), not fetched ad hoc mid-session.
- **Note on ghosting detection:** this depends entirely on diarization quality (speaker labels staying consistent across the session). If diarization proves unreliable or too heavy for available compute, fall back to a simpler proxy: total speaking-time balance across detected speakers, without per-identity tracking — still useful signal, lower engineering risk.


**3. Post-Session Report Agent**
- Input: full session flag log from Redis (pacing, clarity, wrong_answer, confusion, disengagement flags)
- Output: structured report covering — what confused students, which questions/activities students got wrong (and how often), which students/speakers showed disengagement or went quiet, what needs reinforcement next time, suggested adjustments to the instructor's delivery style — becomes input context for next Setup Agent call (cross-session memory)

---

## 6a. Flag Schema & Enum — the Stream Judge ↔ Report Agent Contract

This is the concrete contract both of Sondos's pieces (Stream Judge writes it, Report Agent reads it) must import from `shared/`, not redefine locally. Locking this before either piece is built is the single highest-value thing to do together on Day 1.

**Decision: flag `message` is templated, keyed by `flag_type` — not LLM-generated per flag.** Given the timeline, a fixed template per flag type (filled in with the specific details) is faster, cheaper, and far more predictable under time pressure than asking the LLM to compose a natural-sounding message for every single flag. Save LLM-generated prose for the Report Agent's final narrative, where a bit of natural language actually adds value — not for every real-time flag, where speed and reliability matter more.

```python
# shared/enums/flag_type.py
from enum import Enum

class FlagType(str, Enum):
    PACING = "pacing"                      # teacher-side
    CLARITY = "clarity"                    # teacher-side
    CONFUSION = "confusion"                # student-side
    WRONG_ANSWER = "wrong_answer"          # student-side
    UNCERTAIN_ANSWER = "uncertain_answer"  # student-side, LLM's own verdict — see below, no ASR confidence exists to pre-filter this
    DISENGAGEMENT = "disengagement"        # student-side, ghosting/participation gap


class FlagSeverity(str, Enum):
    INFO = "info"        # worth noting in the report, not urgent live
    WARNING = "warning"  # worth a live nudge to the instructor


# Templates keyed by FlagType — filled in with the flag's specific details.
# Kept alongside the enum since they're a direct function of flag_type.
FLAG_MESSAGE_TEMPLATES: dict[FlagType, str] = {
    FlagType.PACING: "Pacing check: this section is running {detail} for a {audience_level} audience — consider adjusting speed.",
    FlagType.CLARITY: "Clarity check: the explanation style here may not match a {audience_level} audience — consider re-explaining with simpler terms.",
    FlagType.CONFUSION: "A student expressed confusion: \"{detail}\"",
    FlagType.WRONG_ANSWER: "Student answered incorrectly on: \"{question}\" (expected: {expected_answer})",
    FlagType.UNCERTAIN_ANSWER: "Couldn't confidently judge a student's answer to \"{question}\" — audio was unclear, consider asking them to repeat it.",
    FlagType.DISENGAGEMENT: "{speaker_id} hasn't participated in a while — consider checking in with them.",
}
```

```python
# shared/schemas/flag.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from shared.enums.flag_type import FlagType, FlagSeverity

class Flag(BaseModel):
    # identity / routing
    session_id: str
    flag_id: str                          # uuid4, set at creation
    timestamp: datetime

    # what happened
    flag_type: FlagType
    severity: FlagSeverity = FlagSeverity.INFO
    message: str                          # rendered from FLAG_MESSAGE_TEMPLATES[flag_type], not LLM-generated per flag

    # who it's about (student-side flags only; None for teacher-side)
    speaker_id: Optional[str] = None      # diarization label, e.g. "speaker_2"

    # correctness-specific fields (only populated for WRONG_ANSWER / UNCERTAIN_ANSWER)
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    student_utterance: Optional[str] = None
    # NOTE: an asr_confidence field originally lived here — removed after
    # verifying against WhisperLiveKit's own docs/API.md and Deepgram-compat
    # source that no real per-line confidence score exists anywhere in its
    # protocol (native /asr has none; Deepgram-compat hardcodes 0.0). See the
    # correction below and in section 7.5.

    # raw source, for debugging / report drill-down
    transcript_chunk: Optional[str] = None
```

**Why it's shaped this way:**
- `flag_type` and `severity` are separate — Report Agent aggregates by type ("3 confusion flags, 1 disengagement"), while `severity` separately controls what actually interrupts the instructor live vs what's report-only. Not every flag needs to ping the dashboard mid-session.
- `speaker_id` is `Optional` since teacher-side flags (pacing, clarity) aren't about any one student — forcing a value there would just create meaningless placeholder data.
- Correctness-specific fields are grouped and all `Optional`, populated only for `WRONG_ANSWER`/`UNCERTAIN_ANSWER` — one schema instead of forking into multiple flag classes.
- `transcript_chunk` stays raw — useful for Report Agent to quote context in the final narrative, and for debugging "why did it flag this?" without re-deriving it from Redis reads.

**Correction, found via later research (worth flagging honestly rather than silently fixing):** this schema originally included an `asr_confidence` field, and `check_answer_correctness` originally took a confidence threshold to gate judgment (skip judging low-confidence transcripts). Verified via WhisperLiveKit's own `docs/API.md` and its Deepgram-compatible endpoint's source that **no real per-line confidence score exists anywhere in its protocol** — the native `/asr` line schema has no such field, and the Deepgram-compat endpoint hardcodes confidence to `0.0`. Enforcing the original gate as designed would have made `check_answer_correctness` return `"uncertain"` unconditionally, silently disabling correctness-checking entirely. **Fix: `asr_confidence` is removed from the schema; uncertainty is now handled entirely by the Judge LLM's own three-way verdict** (it decides "uncertain" from the *content* of a garbled/incomplete/ambiguous transcript, not from a numeric pre-filter fed by data that was never actually available). See section 7.5 for the corrected tool signature.

---

## 7. Roles

| Person | Owns | Notes |
|---|---|---|
| **Ahmed** | Setup Agent (full) + Stream Judge (architecture/ADK wiring) + LiteLLM proxy config + **WhisperLiveKit deployment and the AMD Developer Cloud/ROCm spike (section 5b)** | Containerization/docker-compose moved to a shared task (see below) rather than solely Ahmed's. The WhisperLiveKit/AMD spike was previously unassigned by default — making it explicit here so it doesn't silently pile onto Ahmed's plate mid-week |
| **Sondos** | Stream Judge (LLM judgment logic/prompting, including the two highest-risk pieces — ghosting/diarization tracking and answer-correctness checking) + Post-Session Report Agent (full) + Frontend | NLP background fits judgment-logic design well; taking the minimal frontend piece balances total *item count* against Ahmed's architecture/infra-heavier workstreams |

**Honest note on balance, not just item count:** by raw workstream count this is now roughly even. But it isn't evenly balanced by *risk* — Sondos's core ownership includes the two most technically uncertain features in the whole system (diarization-based ghosting detection, flagged in section 6 as the shakiest piece; and answer-correctness checking, flagged in section 6 as carrying real compounding-error risk from ASR mistakes stacking with LLM judgment mistakes). Ahmed's Setup Agent, by comparison, is the most "solved" piece — single LLM calls, no live audio, no diarization instability. If something misbehaves live during the demo, it's more likely to surface in Sondos's half, not because of anything she did wrong, but because that's where the harder, less-provable-in-advance problems happen to sit. **Both of you should go in aware of this rather than assuming the split is symmetric just because the item counts look close.** Concretely: check in on Sondos's two hardest pieces earlier and more often than a strictly even schedule would suggest, and don't read early struggles there as a sign anything's off — it's the expected shape of the riskier half of the system.

**Containerization/docker-compose:** treat as a shared, incremental task — whoever finishes their own service's Dockerfile first adds it to the shared `docker-compose.yml`, rather than it sitting entirely on Ahmed's plate alongside everything else.

**No dedicated frontend teammate — Sondos owns it as part of the rebalanced split above.** Keep the UI intentionally minimal — a plain HTML+JS dashboard (WhisperLiveKit already ships a usable template at `whisperlivekit/web/live_transcription.html` you can adapt) or a Gradio interface for Setup Agent input/output. Don't let UI polish compete with agent-logic time; judges weight creativity/completeness of the agentic system over visual design on this track.

---

## 7.5 Tools (per agent)

Each ADK agent needs concrete tool functions, not just a prompt — this was missing from the plan. Breaking these out now so tool boundaries are clear before anyone starts coding.

**Setup Agent tools** (`services/setup_agent/tools/`)
- `generate_slides(topic, level, goals)` → slide content via LiteLLM
- `generate_explanations(topic, level)` → level-tailored explanation text
- `generate_activities(topic, level)` → activity/exercise definitions
- `generate_quiz(topic, level)` → **questions + expected answers, structured** — this output is the critical hand-off to Stream Judge for correctness checking, so its schema needs to be locked early (see shared schemas below)
- `compile_session_package(...)` → bundles the above into one object the frontend renders and Stream Judge receives as session config at kickoff

**Stream Judge tools** (`services/stream_judge/tools/`)
- `check_answer_correctness(question, expected_answer, student_utterance)` → correctness judgment via LiteLLM. **Compounding-error mitigation, corrected from an earlier draft:** ASR mistakes and LLM judgment mistakes stack — a mis-transcribed answer gets judged as if it were correct, producing a wrong flag that's the most visible, most embarrassing failure mode in a live demo. The original design gated this on a per-line ASR confidence score — **removed after confirming WhisperLiveKit provides no such score anywhere in its protocol** (native `/asr` has none; Deepgram-compat hardcodes `0.0`); the gate as designed would have made every call return "uncertain" unconditionally. **The actual safeguard: the LLM's output is three-way** — `correct` / `incorrect` / `uncertain` — and the prompt explicitly instructs it to say "uncertain" when the transcript is garbled, incomplete, or genuinely ambiguous, rather than forcing a binary guess. For the staged demo session specifically, script student answers clearly enough that ASR has an easy time — don't test this edge case live in front of judges for the first time.
- `assess_pacing_clarity(transcript_chunk, level)` → teacher-side flag candidate
- `detect_confusion(transcript_chunk)` → student-side flag candidate
- `track_speaker_activity(speaker_id, timestamp)` → maintains per-speaker last-active time; raises disengagement/ghosting flag when a speaker crosses the silence threshold. Falls back to overall speaking-time-balance if diarization is unreliable (per the fallback noted in section 6).
- `write_flag(flag: Flag)` → **thin wrapper tool, backed by raw `redis-py`**. Takes a typed `Flag` Pydantic object (from `shared/schemas/flag.py`) as its only argument and performs the actual `hset`/`xadd` call with a fixed key pattern/serialization defined once in this function. The LLM never constructs raw Redis commands directly — see schema enforcement note below.
- `notify_instructor(flag)` → pushes to live dashboard via WebSocket/SSE

**Report Agent tools** (`services/report_agent/tools/`)
- `fetch_session_flags(session_id: str) -> list[Flag]` → **thin wrapper tool, backed by raw `redis-py`**. Calls the actual Redis read operation (`xrange`/`hgetall`), then parses raw results back into typed `Flag` objects before returning to the agent.
- `aggregate_flags(flags: list[Flag])` → groups/counts by type, student, question — pure domain logic, no Redis involved
- `generate_report(aggregated)` → LLM call producing the structured report
- `push_to_next_setup(report, next_session_id)` → attaches report as context for the next Setup Agent call (closes the loop)

**Schema enforcement — the actual mechanism, not just a prompt instruction:** raw Redis commands (`hset`, `xadd`, `get`, etc.) are generic and don't know anything about your `Flag` shape — exposing them straight to the LLM and relying on prompt wording to keep the shape consistent will drift over time. Instead, only `write_flag` and `fetch_session_flags` are exposed to the agent as tools; ADK derives their tool schema from the Pydantic model + type hints, so the LLM can only call them with arguments matching the `Flag` structure. The key pattern, serialization, and actual Redis call live once inside these two wrapper functions — both of Sondos's pieces import the same `Flag` model from `shared/schemas/flag.py`, so there's exactly one place the shape is defined and exactly one place it's enforced (the function signature), not scattered across prompt text in two different agents.

---

## 8. Repo & Branch Structure

```
ai-session-copilot/
├── docker-compose.yml
├── .env                    # shared root config — see section 5a
├── .env.example
├── README.md
├── services/
│   ├── setup_agent/
│   │   ├── Dockerfile
│   │   ├── main.py            # FastAPI app
│   │   ├── agent.py           # ADK agent def
│   │   ├── tools/
│   │   │   ├── generate_slides.py
│   │   │   ├── generate_explanations.py
│   │   │   ├── generate_activities.py
│   │   │   ├── generate_quiz.py
│   │   │   └── compile_session_package.py
│   │   └── prompts/
│   ├── stream_judge/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── ws_client.py       # connects to whisper-livekit /asr
│   │   ├── tools/
│   │   │   ├── check_answer_correctness.py
│   │   │   ├── assess_pacing_clarity.py
│   │   │   ├── detect_confusion.py
│   │   │   ├── track_speaker_activity.py
│   │   │   ├── write_flag.py      # thin wrapper: typed Flag in → redis-mcp hset/xadd call
│   │   │   └── notify_instructor.py
│   │   └── prompts/
│   ├── report_agent/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── tools/
│   │   │   ├── fetch_session_flags.py  # thin wrapper: redis-mcp read call → parsed into Flag objects
│   │   │   ├── aggregate_flags.py
│   │   │   ├── generate_report.py
│   │   │   └── push_to_next_setup.py
│   │   └── prompts/
│   └── whisper_livekit/       # vendored config/compose override only
│       └── docker-compose.override.yml
├── shared/
│   ├── schemas/
│   │   ├── flag.py            # Flag schema — the Stream Judge ↔ Report Agent contract; enforced via write_flag/fetch_session_flags function signatures, not prompt text
│   │   ├── session_package.py # Setup Agent output — also Stream Judge's session config input
│   │   └── report.py          # Report Agent output — also next Setup Agent's input context
│   ├── enums/
│   │   ├── flag_type.py       # PACING, CLARITY, WRONG_ANSWER, CONFUSION, DISENGAGEMENT, UNCERTAIN_ANSWER (LLM's own verdict — no ASR confidence exists to pre-filter, see section 6)
│   │   └── audience_level.py  # KIDS, YOUTH, ADULTS
│   ├── constants.py           # silence thresholds, Redis key prefixes, default model names
│   ├── mcp_config.py          # MCPToolset connection params for redis-mcp (shared by Stream Judge + Report Agent)
│   └── litellm_config.yaml
├── frontend/
│   └── (minimal UI — see section 3, Tech Stack)
└── tests/
```

**Why this matters beyond tidiness:** `shared/schemas/flag.py` and `shared/enums/flag_type.py` are the actual contract between Sondos's two pieces (Stream Judge writes flags, Report Agent reads them) — this is the schema-lock discussed earlier, now given a concrete file location instead of just a verbal agreement. Same for `session_package.py`, which is the Setup Agent → Stream Judge hand-off needed for answer-correctness checking. Both of you should import these from `shared/`, never redefine flag/session shapes locally inside a service — that's exactly the kind of drift that causes Day-3 integration bugs.

**Branching:**
- `main` — always demo-able
- `feat/setup-agent`, `feat/stream-judge`, `feat/report-agent`, `feat/frontend` — one per owner
- Merge to `main` daily after a working local test, not at the end — avoids Day-4 integration disaster
- Tag `submission` branch/commit at deadline for the actual lablab.ai submission link

---

## 8a. Local Development Workflow

`docker compose up --build` rebuilds everything on every change — fine for a final integration check, too slow for active development. Three practical options, in order of preference for actual day-to-day work:

**Approach A — infra in Docker, your own service local with hot-reload (recommended default):**
```bash
docker compose up redis litellm-proxy -d   # leave running
cd services/setup_agent
uv venv
uv pip install -e .          # confirmed working — see correction below
uv run uvicorn main:app --port 8001 --reload
```
Restarts on every file save. Requires `uv` installed locally.

**Approach B — everything in Docker.** `docker compose up --build`. Simplest, but every change needs a rebuild — use for final checks, not iteration.

**Approach C — both of you running your own service locally against shared infra containers**, same as Approach A but each on your own port, both pointing at the same `redis`/`litellm-proxy` containers. Good once you're both actively coding against the same running Redis/proxy without stepping on each other's rebuilds.

**Correction to a claim that circulated about this repo — verified empirically, not assumed:** it was suggested that `uv pip install -r pyproject.toml` (used in all three Dockerfiles) "won't work" because `-r` supposedly only reads requirements.txt format and would reject TOML. **This is incorrect for a properly-formatted `pyproject.toml` like ours** — tested directly: `uv pip install --system --no-cache -r pyproject.toml` against our actual `setup_agent/pyproject.toml` successfully installed all 40+ packages (FastAPI, LiteLLM stack, Pydantic, transitive deps) with zero errors. The confusion likely stems from a real but unrelated GitHub issue where `uv pip compile` had generated an *invalid, malformed* pyproject.toml (in requirements.txt format by mistake) — a broken input file, not a case of `-r` rejecting valid TOML. Don't "fix" the Dockerfiles based on this claim; they were already correct.

**What *was* a real gap, now fixed:** `uv pip install -e .` (needed for the local-dev Approach A above) genuinely did fail initially — hatchling couldn't auto-detect what to package from our flat `main.py`/`tools/`/`prompts/` layout (no directory matching the project name). Fixed by adding `[build-system]` + `[tool.hatch.build.targets.wheel] include = [...]` to all three `pyproject.toml` files — verified working via an actual `uv pip install -e .` run in a clean venv afterward.

**Also fixed: `google-adk` alone isn't enough for LiteLLM routing.** `from google.adk.models.lite_llm import LiteLlm` raises `ImportError` without the `[extensions]` extra. All three `pyproject.toml` files now declare `"google-adk[extensions]"` instead of plain `"google-adk"` + a separate `"litellm"` line (the extra pulls in what's needed). Every `agent.py` now correctly wraps its model as `LiteLlm(model="openai/<alias>", api_base="http://litellm-proxy:4000/v1", ...)` — pointing at *our own* proxy container — rather than a bare model string, which would have bypassed the proxy (and the `LLM_PROVIDER` toggle) entirely and called a provider directly. Verified by actually constructing all three agents against the real installed package.

---

## 8b. Implementation Status

Snapshot as of the last scaffolding pass — update as you build.

| Path | Owner | Status |
|---|---|---|
| `shared/schemas/` (flag, session_package, report) | Both | ✅ Done, functionally tested |
| `shared/enums/` (FlagType, FlagSeverity, AudienceLevel, message templates) | Both | ✅ Done |
| `shared/constants.py` | Both | ✅ Done (no longer includes the removed `ASR_LOW_CONFIDENCE_THRESHOLD` — see section 6a) |
| `shared/run_agent.py` | Both | ✅ Ready, verified against real `google-adk` |
| `services/setup_agent/` | Ahmed | `agent.py` ✅, all 5 tools scaffolded (LLM calls still `TODO`), `POST /setup` wired to raise the stub deliberately |
| `services/stream_judge/` | Sondos + Ahmed | `agent.py` ✅, all 6 tools scaffolded (`write_flag`, `track_speaker_activity` fully implemented; `check_answer_correctness`, `assess_pacing_clarity`, `detect_confusion` need their LLM calls; `notify_instructor` implemented), `transcript_receiver.py` wired |
| `services/report_agent/` | Sondos | `agent.py` ✅, all 4 tools scaffolded (`fetch_session_flags`, `aggregate_flags` fully implemented; `generate_report`, `push_to_next_setup` need wiring) |
| `frontend/` | Sondos | ✅ Capture pipeline complete and unit-tested (downsampling math, PCM conversion, diff-protocol reconstruction all verified against real numbers/documented examples) — `getDisplayMedia` → AudioWorklet → WhisperLiveKit → Stream Judge forwarding, all real code, not pseudocode |
| `docker-compose.yml` | Shared | ✅ All 7 services wired, WhisperLiveKit builds from its real repo (no fabricated image), CORS added to all three FastAPI services |
| `prompts/` | Both | Placeholder READMEs only — actual prompt content is genuinely still to-do for whoever wires each tool's LLM call |

**What "TODO: wire up a LiteLLM call" actually means in the remaining files:** the function signature, imports, and calling context are all real and tested — what's missing is the actual prompt text and the `await litellm.acompletion(...)` (or equivalent) call inside. This is deliberate scoping, not an oversight: writing good prompts is domain work you two should do deliberately, not something to fabricate confidently in a planning pass.

---

## 9. Timeline (July 6–11)

**Day 0 (before July 6):**
- Both register AMD ADP + lablab.ai hackathon page; request AMD Developer Cloud credit (2-3 day approval — do this now, since it likely won't land until Day 2-3 of the actual build)
- **Fallback trigger:** if AMD Developer Cloud credit isn't live by end of Day 2, proceed on Fireworks-only for all LLM calls and treat AMD Developer Cloud as a Day-4/5 addition if it lands late — don't let the whole build stall waiting on it
- Lock Redis flag schema together (30 min sync)
- Repo scaffolded, docker-compose skeleton up, litellm-proxy running with both Fireworks + AMD Cloud configs stubbed
- Agree on the local-dev/cloud-instance workflow: build and test locally first, keep `main` clean, pull `main` onto the AMD Cloud instance for hardware-specific checks only once it's provisioned (see section 5b)

**Day 1 (Jul 6):**
- Get WhisperLiveKit running end-to-end locally (mic → transcript) — de-risk this first, it's your critical dependency
- **WhisperLiveKit's `/asr` response protocol is now confirmed from its official `docs/API.md`** (not guessed): `config` message on connect, then `snapshot`/`diff` messages with `new_lines`/`lines_pruned`, each line `{speaker: int, text: str|null, start, end}`, `speaker === -2` meaning a silence segment, and `ready_to_stop` at the end. **No confidence field exists anywhere in this protocol** — confirmed via the same docs and the Deepgram-compatible endpoint's source (hardcodes `0.0`) — this is why `check_answer_correctness` no longer takes a confidence parameter; see section 6/7.5. `frontend/app.js` already implements this real protocol (`mode=diff`, line reconstruction, silence-segment filtering) and its diff-reconstruction logic has been unit-tested against the documented example payloads. Still worth a real end-to-end check against the running server on Day 1, since documentation and implementation can drift.
- Setup Agent: basic LLM call wired through LiteLLM, one hardcoded topic → slides+quiz output
- Frontend: capture flow already scaffolded (`frontend/index.html`, `app.js`, `pcm-worklet-processor.js`) — getDisplayMedia → AudioWorklet → 16kHz PCM → WhisperLiveKit, with confirmed chunks forwarded to Stream Judge. Downsampling/PCM-conversion math is unit-tested; the WhisperLiveKit response parsing above is the piece that still needs real verification.

**Day 2 (Jul 7):**
- Stream Judge: wire WhisperLiveKit WebSocket → confirmed chunk → first LLM judgment call (teacher-side only first, student-side next)
- Redis flag write path working
- Frontend: live dashboard skeleton receiving flags
- If AMD Developer Cloud credit has landed: run the `--backend whisper` + ROCm PyTorch spike on the cloud instance now (section 5b) — don't let it block Stream Judge's core logic, run it in parallel or after core wiring is solid
- **Cut trigger:** if only teacher-side flags are working by end of Day 2, that's an acceptable checkpoint — student-side (correctness/ghosting) can compress into Day 3, but if *neither* side is producing flags yet, cut ghosting detection from the MVP now rather than Day 4

**Day 3 (Jul 8):**
- Stream Judge: add student-side signals
- Report Agent: aggregate Redis flags → first structured report draft
- Start wiring report → next Setup Agent call (the loop-closing piece)

**Day 4 (Jul 9):**
- Full loop test: Setup → live session (staged) → flags → Report → feeds next Setup
- Fix integration bugs — expect this day to be mostly debugging, not new features
- Frontend polish

**Day 5 (Jul 10):**
- Freeze features. Record demo video/run-through.
- Write submission text (problem, solution, AMD platform usage, market potential)
- Confirm containerization actually works via `docker compose up --build` from clean

**Day 6 (Jul 11, before 15:00 UTC):**
- Final submission on lablab.ai
- Buffer time for last-minute Docker/credential issues — do NOT submit at 14:55

---

## 10. Submission Checklist

- [ ] All services run via single `docker compose up --build`
- [ ] Uses AMD Developer Cloud for at least one real inference call (explicit judging criterion)
- [ ] MIT-compliant / original code (per lablab.ai rules)
- [ ] Demo video or live run-through showing full loop: Setup → Live Judge → Report → next Setup
- [ ] Submission text covers: problem, solution, AMD platform usage, product/market potential
- [ ] Repo public/accessible to judges
- [ ] Team page on lablab.ai has all members added
- [ ] (Optional, low-cost) At least one agent's LLM calls routed through a Gemma model — qualifies for the "Best Use of Gemma Models" side challenge, no separate sign-up needed

---

## Open Questions to Resolve With Team Before Building

1. Live notifier and report aggregator — same Redis flag schema, confirmed? (enforced via `shared/schemas/flag.py`, read/written through the raw `redis-py`-backed `write_flag`/`fetch_session_flags` wrapper functions — see section 6)
2. Frontend build approach — Gradio vs adapted WhisperLiveKit HTML template vs minimal React (owned by Sondos per section 7 — her call, but worth deciding together on Day 0/1)
3. Which specific model(s) on AMD Developer Cloud vs Fireworks for each agent call — decide once credits land
4. Fallback plan if WhisperLiveKit's diarization proves too heavy for available compute (drop diarization, single-speaker assumption for MVP demo)
5. Confirm `--backend whisper` (ROCm PyTorch path, section 5b) actually runs on the AMD Developer Cloud instance once provisioned — reasonably confirmed by AMD's own published results, but still verify on your specific GPU before relying on it for the demo
