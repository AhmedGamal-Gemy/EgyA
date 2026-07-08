from shared.enums.flag_type import AudienceLevel


def build_slides_prompt(topic: str, audience_level: AudienceLevel, goals: list[str]) -> str:
    goals_text = "\n".join(f"- {g}" for g in goals)
    return (
        f"You are an expert educator preparing slide content for a {audience_level.value} audience.\n"
        f"Topic: {topic}\n"
        f"Session goals:\n{goals_text}\n\n"
        "Generate 5-8 slide titles, each with a 1-2 sentence description of what that slide covers.\n"
        "Tailor the complexity, vocabulary, and examples to the audience level.\n"
        "Output ONLY valid JSON — an array of strings. No markdown, no extra text.\n"
        'Example: ["1. What is Photosynthesis — Define photosynthesis and why it matters", '
        '"2. The Equation — Break down the chemical reaction step by step"]'
    )
