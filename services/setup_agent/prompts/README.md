# Prompts — Setup Agent

Placeholder. Each tool in `../tools/` currently has a `TODO: wire up a
LiteLLM call` comment where a real prompt is needed. Once written, prompt
templates for `generate_slides`, `generate_explanations`,
`generate_activities`, and `generate_quiz` belong in this directory as
separate files (e.g. `generate_quiz_prompt.py` holding a prompt template
string/function), not inline in the tool files, so they're easy to iterate
on independently of the calling code.

Reminder from the plan (section 6a): `generate_quiz`'s prompt MUST
constrain answers to short/discrete form — this is not optional, it's what
makes Stream Judge's correctness-checking tractable at all.
