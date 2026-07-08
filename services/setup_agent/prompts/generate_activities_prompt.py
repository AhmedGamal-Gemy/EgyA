from shared.enums.flag_type import AudienceLevel


def build_activities_prompt(topic: str, audience_level: AudienceLevel) -> str:
    return (
        f"You are an expert educator designing in-class activities for a {audience_level.value} audience.\n"
        f"Topic: {topic}\n\n"
        "Create 2-4 engaging activities that reinforce the topic. Each activity must have:\n"
        "- A short title\n"
        "- Clear step-by-step instructions for the instructor to run it\n\n"
        "Output ONLY valid JSON — an array of objects with 'title' and 'instructions' keys. "
        "No markdown, no extra text.\n"
        'Example: [{"title": " photosynthesis RAFT writing", '
        '"instructions": " Each student picks a role (sunlight, water, CO2), '
        "writes a short 'day in the life' paragraph from that perspective.\"}"
        ', {"title": "Equation relay", '
        '"instructions": "Split the class into teams. Each team races to correctly write '
        'and label the photosynthesis equation on the board."}]'
    )
