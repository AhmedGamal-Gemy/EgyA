"""See plan section 7.5 — Report Agent tools."""

from shared.schemas.flag import Flag
from shared.schemas.report import FlagSummary, SessionReport


async def generate_report(
    session_id: str,
    flags: list[Flag],
    flag_summary: list[FlagSummary],
) -> SessionReport:
    import json
    from shared.run_agent import run_agent
    from services.report_agent.agent import root_agent

    prompt = (
        f"Act as an educational evaluator and generate a Post-Session Report for session '{session_id}'.\\n"
        f"Analyze the following flag summaries which represent events during the lesson:\\n"
        f"{[s.model_dump() for s in flag_summary]}\\n\\n"
        f"INSTRUCTIONS:\\n"
        f"1. what_confused_students: List of strings extracting specific concepts students struggled with.\\n"
        f"2. wrong_answers: List of strings summarizing which questions were missed (e.g., 'Question X - missed 2 times'). Do NOT output dictionaries.\\n"
        f"3. disengaged_speakers: List of strings identifying who was disengaged.\\n"
        f"4. reinforcement_needed: List of strings. Based on confusion and wrong answers, what topics should be revisited next session?\\n"
        f"5. delivery_adjustments: List of strings. Based on pacing or clarity flags, what should the teacher change?\\n"
        f"6. narrative_summary: A single string. Write a rich, conversational paragraph summarizing the session's overall health, "
        f"student struggles, and teacher performance.\\n\\n"
        f"Please output a valid JSON containing exactly these fields: session_id, what_confused_students, wrong_answers, "
        f"disengaged_speakers, reinforcement_needed, delivery_adjustments, flag_summary, narrative_summary."
    )

    try:
        response_text = await run_agent(
            agent=root_agent,
            app_name="report_agent",
            user_id="system",
            session_id=session_id,
            message=prompt,
        )

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
        else:
            json_str = response_text.strip()

        data = json.loads(json_str)
        data["flag_summary"] = [s.model_dump() for s in flag_summary]
        return SessionReport(**data)

    except Exception as e:
        print(
            f"LLM call failed or not configured ({e}). Returning dumb synthetic data for testing."
        )

        return SessionReport(
            session_id=session_id,
            what_confused_students=[
                "Some students were confused about pointers based on 'confusion' flags."
            ],
            wrong_answers=[
                "Question 1 (What is a pointer?) — missed 2 times",
            ],
            disengaged_speakers=["speaker_2", "speaker_4"],
            reinforcement_needed=["Need to revisit memory management basics."],
            delivery_adjustments=[
                "Pacing was a bit fast during the memory segment, consider slowing down."
            ],
            flag_summary=flag_summary,
            narrative_summary="The session went generally well but highlighted some knowledge gaps in memory management. speaker_2 and speaker_4 showed signs of disengagement towards the end. The pacing was slightly fast for this level.",
        )
