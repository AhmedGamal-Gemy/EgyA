"""Setup Agent — ADK agent definition. See plan section 6/7.5 for the tool
list this agent is meant to orchestrate (generate_slides, generate_explanations,
generate_activities, generate_quiz, compile_session_package).
"""

import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Routes through OUR OWN litellm-proxy container (shared/litellm_config.yaml),
# not litellm's provider integrations directly — this is what actually lets
# the LLM_PROVIDER env toggle (see shared/constants.py, plan section 5a)
# switch every agent between Fireworks/AMD Developer Cloud/Ollama with one
# config change, since the proxy holds the real provider routing, not this
# agent code.
LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm-proxy:4000")
# model_name alias from shared/litellm_config.yaml's model_list —
# "openai/" prefix tells litellm to treat this as an OpenAI-compatible
# endpoint (which our own proxy is), not call Fireworks/AMD directly.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
DEFAULT_MODEL_ALIAS = f"openai/{LLM_PROVIDER}-default"

# TODO: import the actual tool functions from ./tools/ once written, e.g.:
#   from tools.generate_slides import generate_slides
#   from tools.generate_quiz import generate_quiz
# and pass them in `tools=[...]` below.

root_agent = Agent(
    name="setup_agent",
    model=LiteLlm(
        model=DEFAULT_MODEL_ALIAS,
        api_base=f"{LITELLM_PROXY_URL}/v1",
        api_key=os.environ.get("LITELLM_MASTER_KEY", "not-needed-for-local-proxy"),
    ),
    instruction=(
        "You are the Setup Agent for an AI Education Session Copilot. "
        "Given a topic, audience level, and session goals, generate slides, "
        "explanations, activities, and a short quiz with discrete/short "
        "expected answers (not open-ended) — see plan section 6a on why "
        "quiz answers must stay short/discrete for correctness-checking "
        "downstream to be reliable."
    ),
    tools=[],  # TODO: populate once tools/*.py are implemented
)
