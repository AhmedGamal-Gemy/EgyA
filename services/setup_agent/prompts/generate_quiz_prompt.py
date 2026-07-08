from shared.enums.flag_type import AudienceLevel


def build_quiz_prompt(topic: str, audience_level: AudienceLevel) -> str:
    return (
        f"You are an expert educator creating a short quiz for a {audience_level.value} audience.\n"
        f"Topic: {topic}\n\n"
        "Create 3-5 quiz questions that test the core concepts.\n\n"
        "CRITICAL CONSTRAINT — questions MUST have short, discrete answers "
        "(one word or a short phrase). "
        "This is required because a downstream LLM will compare the spoken transcript "
        "of a student's answer against the expected_answer field — "
        "open-ended or essay-style answers cannot be judged reliably.\n\n"
        "Bad examples (open-ended): 'Explain how photosynthesis works', "
        "'Why is the water cycle important?'\n"
        "Good examples (short-answer): 'What gas do plants absorb?', "
        "'Name the process by which plants make food', "
        "'What is the chemical symbol for water?'\n\n"
        "Output ONLY valid JSON — an array of objects with 'question' and 'expected_answer' keys. "
        "No markdown, no extra text.\n"
        'Example: [{"question": "What gas do plants absorb from the atmosphere?", '
        '"expected_answer": "Carbon dioxide (CO2)"}, '
        '{"question": "What is the main pigment in plant leaves that captures sunlight?", '
        '"expected_answer": "Chlorophyll"}]'
    )
