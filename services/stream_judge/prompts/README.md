# Prompts — Stream Judge

Placeholder. Prompts needed for `check_answer_correctness`,
`assess_pacing_clarity`, and `detect_confusion` (see `../tools/`).

Important reminder baked into the plan (section 6): there is no ASR
confidence score available from WhisperLiveKit. The
`check_answer_correctness` prompt is the ONLY place uncertainty is
handled — it must explicitly instruct the model to answer "uncertain"
rather than force a correct/incorrect guess when the transcript looks
garbled, incomplete, or ambiguous. Don't lose this instruction when writing
the real prompt.
