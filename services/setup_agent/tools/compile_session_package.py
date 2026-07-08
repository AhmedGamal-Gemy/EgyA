import asyncio
import json
import os
import re

from litellm import acompletion
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

import litellm
from shared.constants import DIRECT_LLM_MODEL, LITELLM_PROXY_URL, LLM_PROVIDER, LLM_TEMPERATURE
from shared.enums.flag_type import AudienceLevel
from shared.schemas.session_package import Activity, QuizQuestion, SessionPackage
from prompts.generate_slides_prompt import build_slides_prompt
from prompts.generate_explanations_prompt import build_explanations_prompt
from prompts.generate_activities_prompt import build_activities_prompt
from prompts.generate_quiz_prompt import build_quiz_prompt


@retry(
    stop=stop_after_attempt(int(os.environ.get("LLM_RETRY_ATTEMPTS", "3"))),
    wait=wait_exponential(multiplier=1, min=int(os.environ.get("LLM_RETRY_MIN", "2")), max=int(os.environ.get("LLM_RETRY_MAX", "10"))),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.ServiceUnavailableError))
)
async def _call_llm(prompt: str):
    use_direct_groq = bool(os.environ.get("GROQ_API_KEY"))
    model = DIRECT_LLM_MODEL if use_direct_groq else f"openai/{LLM_PROVIDER}-default"
    api_base = None if use_direct_groq else f"{LITELLM_PROXY_URL}/v1"
    api_key = os.environ.get("GROQ_API_KEY") if use_direct_groq else os.environ.get("LITELLM_MASTER_KEY", "not-needed")
    response = await acompletion(
        model=model, api_base=api_base, api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
        temperature=LLM_TEMPERATURE,
    )
    return (response.choices[0].message.content or "")


async def _call_generate_slides(topic: str, audience_level: AudienceLevel, goals: list[str]) -> list[str]:
    try:
        content = await _call_llm(build_slides_prompt(topic, audience_level, goals))
        return _extract_json_list(content)
    except Exception as e:
        print(f"[setup_agent] generate_slides failed: {e}")
        return [f"1. Introduction to {topic}", f"2. Key Concepts", f"3. Summary"]


async def _call_generate_explanations(topic: str, audience_level: AudienceLevel) -> list[str]:
    try:
        content = await _call_llm(build_explanations_prompt(topic, audience_level))
        return _extract_json_list(content)
    except Exception as e:
        print(f"[setup_agent] generate_explanations failed: {e}")
        return [f"Introduction to {topic}", f"Key concepts explained"]


async def _call_generate_activities(topic: str, audience_level: AudienceLevel) -> list[Activity]:
    try:
        content = await _call_llm(build_activities_prompt(topic, audience_level))
        data = json.loads(_strip_fences(content))
        return [Activity(**item) for item in data]
    except Exception as e:
        print(f"[setup_agent] generate_activities failed: {e}")
        return [Activity(title=f"Group discussion on {topic}", instructions="Discuss the key concepts.")]


async def _call_generate_quiz(topic: str, audience_level: AudienceLevel) -> list[QuizQuestion]:
    try:
        content = await _call_llm(build_quiz_prompt(topic, audience_level))
        data = json.loads(_strip_fences(content))
        return [QuizQuestion(**item) for item in data]
    except Exception as e:
        print(f"[setup_agent] generate_quiz failed: {e}")
        return [QuizQuestion(question=f"What is {topic}?", expected_answer="A concept")]


def _strip_fences(content: str) -> str:
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    return content


def _extract_json_list(content: str) -> list[str]:
    data = json.loads(_strip_fences(content))
    if not isinstance(data, list):
        raise ValueError("LLM did not return a list")
    return data


async def compile_session_package(
    session_id: str,
    topic: str,
    audience_level: AudienceLevel,
    goals: list[str],
    previous_session_report_summary: str | None = None,
) -> SessionPackage:
    slides, explanations, activities, quiz = await asyncio.gather(
        _call_generate_slides(topic, audience_level, goals),
        _call_generate_explanations(topic, audience_level),
        _call_generate_activities(topic, audience_level),
        _call_generate_quiz(topic, audience_level),
    )
    return SessionPackage(
        session_id=session_id, topic=topic, audience_level=audience_level, goals=goals,
        slides=slides, explanations=explanations, activities=activities, quiz=quiz,
        previous_session_report_summary=previous_session_report_summary,
    )
