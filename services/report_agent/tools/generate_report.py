import json
import os
from shared.schemas.flag import Flag
from shared.schemas.report import FlagSummary, SessionReport
from litellm import acompletion
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import litellm

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.ServiceUnavailableError))
)
async def _call_llm_with_retry(*args, **kwargs):
    return await acompletion(*args, **kwargs)

async def generate_report(
    session_id: str,
    flags: list[Flag],
    flag_summary: list[FlagSummary],
) -> SessionReport:
    prompt = (
        f"You are an Expert Educational Evaluator generating a Post-Session Report for session '{session_id}'.\n"
        f"Analyze the following aggregated flag summaries representing events during the lesson:\n"
        f"{[s.model_dump() for s in flag_summary]}\n\n"
        "INSTRUCTIONS FOR YOUR ANALYSIS:\n"
        "1. 'what_confused_students': Array of strings extracting the specific core concepts students struggled with based on confusion flags.\n"
        "2. 'wrong_answers': Array of strings summarizing which specific questions were missed and how many times (e.g., 'Question X - missed 2 times'). Do NOT output dictionaries here.\n"
        "3. 'disengaged_speakers': Array of strings identifying participants who were flagged for disengagement.\n"
        "4. 'reinforcement_needed': Array of strings. Based on the confusion and wrong answers, suggest specific topics to revisit next session.\n"
        "5. 'delivery_adjustments': Array of strings. Based on pacing or clarity flags, suggest actionable adjustments for the teacher's speaking style or speed.\n"
        "6. 'improvement_tips': Array of strings. Based on the overall flow, suggest tips to improve the quality of the NEXT session (e.g., use more visual aids, add interactive quizzes, pair students up, etc.).\n"
        "7. 'narrative_summary': A single string containing a rich, professional paragraph summarizing the overall health of the session, major student struggles, and teacher performance.\n\n"
        "Output ONLY valid JSON containing EXACTLY these keys: session_id, what_confused_students, wrong_answers, "
        "disengaged_speakers, reinforcement_needed, delivery_adjustments, improvement_tips, narrative_summary."
    )

    use_direct_groq = bool(os.environ.get("GROQ_API_KEY"))
    model = "groq/llama-3.3-70b-versatile" if use_direct_groq else "openai/groq-default"
    api_base = None if use_direct_groq else os.environ.get("LITELLM_PROXY_URL", "http://localhost:4000") + "/v1"
    api_key = os.environ.get("GROQ_API_KEY") if use_direct_groq else "not-needed"

    try:
        response = await _call_llm_with_retry(
            model=model,
            api_base=api_base,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        data = json.loads(content)
        # Force session_id and original flag_summary into the final dict
        data["session_id"] = session_id
        data["flag_summary"] = [s.model_dump() for s in flag_summary]
        
        return SessionReport(**data)

    except Exception as e:
        print(f"[generate_report] LLM call failed after retries: {e}")
        # Minimal clean fallback
        return SessionReport(
            session_id=session_id,
            what_confused_students=["Error generating report insights."],
            wrong_answers=[],
            disengaged_speakers=[],
            reinforcement_needed=[],
            delivery_adjustments=[],
            improvement_tips=[],
            flag_summary=[s.model_dump() for s in flag_summary],
            narrative_summary="The AI was unable to generate a narrative summary due to an API error."
        )
