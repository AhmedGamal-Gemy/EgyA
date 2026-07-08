from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from shared.constants import LITELLM_PROXY_URL, LLM_PROVIDER
from tools.compile_session_package import compile_session_package

root_agent = Agent(
    name="setup_agent",
    model=LiteLlm(
        model=f"openai/{LLM_PROVIDER}-default",
        api_base=f"{LITELLM_PROXY_URL}/v1",
        api_key="not-needed",
    ),
    instruction=(
        "You are the Setup Agent for an AI Education Session Copilot. "
        "Given a topic, audience level, and session goals, generate slides, "
        "explanations, activities, and a short quiz with discrete/short "
        "expected answers (not open-ended) — see plan section 6a on why "
        "quiz answers must stay short/discrete for correctness-checking "
        "downstream to be reliable."
    ),
    tools=[compile_session_package],
)
