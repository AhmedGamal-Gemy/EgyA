"""Shared ADK Runner helper — written once, reused by Setup Agent, Stream
Judge, and Report Agent. See plan section 4/4a: this replaced an earlier
A2A-based design, which was reconsidered as overkill for a single-team,
same-repo, same-framework build.
"""

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def run_agent(agent: Agent, app_name: str, user_id: str, session_id: str, message: str) -> str:
    """Runs a single turn against an ADK agent and returns the final text response.

    Creates (or reuses) an in-memory session per session_id — good enough for
    a hackathon; swap InMemorySessionService for a persistent one later if
    cross-restart memory is ever needed.
    """
    session_service = InMemorySessionService()
    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=message)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    return final_text
