import os

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
REDIS_FLAG_KEY_PREFIX = "session:flags:"  # + session_id, a Redis stream (XADD/XRANGE)

# ASR / Stream Judge batching
BATCH_STRATEGY = os.environ.get("BATCH_STRATEGY", "vad_pause")  # vs "fixed_window"
DISENGAGEMENT_SILENCE_THRESHOLD_SECONDS = 120  # a speaker silent this long may be "ghosting"

# NOTE: there used to be an ASR_LOW_CONFIDENCE_THRESHOLD constant here, gating
# correctness-checking on a per-line ASR confidence score. Removed — confirmed
# via WhisperLiveKit's own docs/API.md and Deepgram-compat source that neither
# the native /asr protocol nor the Deepgram-compatible endpoint provides a real
# confidence score (Deepgram-compat hardcodes 0.0). Enforcing that gate would
# have made every correctness check return "uncertain" unconditionally. See
# plan section 6 — uncertainty is now handled entirely by the Judge LLM's own
# three-way verdict (correct/incorrect/uncertain), not a numeric ASR pre-filter.

# LLM routing
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "fireworks")  # "fireworks" | "amd_cloud" | "ollama"
LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm-proxy:4001")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
DIRECT_LLM_MODEL = os.environ.get("DIRECT_LLM_MODEL", "groq/llama-3.3-70b-versatile")
ASR_POLICY = os.environ.get("ASR_POLICY", "localagreement")  # vs "simulstreaming"
ASR_BACKEND = os.environ.get("ASR_BACKEND", "whisper")  # vanilla PyTorch — see plan section 5b
                                                          # ("faster-whisper" default has no ROCm support)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")
