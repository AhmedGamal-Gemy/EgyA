"""Post-Session Report Agent — ADK agent definition. See plan section 6/7.5
for the tool list: fetch_session_flags, aggregate_flags, generate_report,
push_to_next_setup.
"""

import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# See setup_agent/agent.py for why this routes through our own litellm-proxy
# rather than calling a provider directly.
LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm-proxy:4000")
DEFAULT_MODEL_ALIAS = "openai/fireworks-default"

# TODO: import and wire actual tool functions once written, e.g.:
#   from tools.fetch_session_flags import fetch_session_flags
#   from tools.aggregate_flags import aggregate_flags
#   from tools.generate_report import generate_report
#   from tools.push_to_next_setup import push_to_next_setup

root_agent = Agent(
    name="report_agent",
    model=LiteLlm(
        model=DEFAULT_MODEL_ALIAS,
        api_base=f"{LITELLM_PROXY_URL}/v1",
        api_key=os.environ.get("LITELLM_MASTER_KEY", "not-needed-for-local-proxy"),
    ),
    instruction=(
        "You are the Post-Session Report Agent. Given a session's full flag "
        "log, produce a structured report: what confused students, which "
        "quiz questions were missed and how often, which students showed "
        "disengagement, what needs reinforcement next time, and suggested "
        "delivery adjustments. This report becomes context for the next "
        "Setup Agent call (cross-session memory) — see plan section 6."
    ),
    tools=[],  # TODO: populate once tools/*.py are implemented
)
