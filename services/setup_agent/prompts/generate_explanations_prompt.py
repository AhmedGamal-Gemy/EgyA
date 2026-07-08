from shared.enums.flag_type import AudienceLevel


def build_explanations_prompt(topic: str, audience_level: AudienceLevel) -> str:
    return (
        f"You are an expert educator writing level-tailored explanations for a {audience_level.value} audience.\n"
        f"Topic: {topic}\n\n"
        "Write 3-5 clear explanations covering the core concepts of this topic. Each explanation should:\n"
        "- Use vocabulary and analogies appropriate for the audience level\n"
        "- Build from simple to more nuanced ideas\n"
        "- Stand alone as a self-contained mini-lesson\n\n"
        "Output ONLY valid JSON — an array of strings. No markdown, no extra text.\n"
        'Example: ["Photosynthesis is how plants make their own food using sunlight, '
        'water, and carbon dioxide.", "The process happens inside tiny cell parts called chloroplasts."]'
    )
