"""Stream Judge — ADK agent definition. See plan section 6/7.5 for the tool
list: check_answer_correctness, assess_pacing_clarity, detect_confusion,
track_speaker_activity, write_flag, notify_instructor.
"""

import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# See setup_agent/agent.py for why this routes through our own litellm-proxy
# rather than calling a provider directly.
LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm-proxy:4001")
DEFAULT_MODEL_ALIAS = "openai/fireworks-default"

# TODO: import and wire actual tool functions once written, e.g.:
#   from tools.check_answer_correctness import check_answer_correctness
#   from tools.assess_pacing_clarity import assess_pacing_clarity
#   from tools.detect_confusion import detect_confusion
#   from tools.track_speaker_activity import track_speaker_activity, check_disengagement
#   from tools.write_flag import write_flag
#   from tools.notify_instructor import notify_instructor

root_agent = Agent(
    name="stream_judge_agent",
    model=LiteLlm(
        model=DEFAULT_MODEL_ALIAS,
        api_base=f"{LITELLM_PROXY_URL}/v1",
        api_key=os.environ.get("LITELLM_MASTER_KEY", "not-needed-for-local-proxy"),
    ),
    instruction=(
        "You are the Stream Judge for a live teaching session. Given a "
        "confirmed transcript line and session context (quiz questions/"
        "expected answers from the Setup Agent), assess: teacher-side "
        "pacing/clarity, and student-side confusion/correctness/"
        "disengagement. For correctness checks specifically, output one of "
        "correct/incorrect/uncertain — say 'uncertain' rather than guessing "
        "when the transcript is garbled, incomplete, or genuinely ambiguous "
        "(see plan section 6 — there is no ASR confidence score available "
        "to pre-filter this, so the judgment call is entirely yours)."
    ),
    tools=[],  # TODO: populate once tools/*.py are implemented
)
