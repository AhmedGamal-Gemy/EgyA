import os
from typing import Literal
from litellm import acompletion
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import litellm

CorrectnessVerdict = Literal["correct", "incorrect", "uncertain"]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.ServiceUnavailableError))
)
async def _call_llm_with_retry(*args, **kwargs):
    return await acompletion(*args, **kwargs)

async def check_answer_correctness(
    question: str,
    expected_answer: str,
    student_utterance: str,
) -> CorrectnessVerdict:
    prompt = (
        f"Question asked: {question}\n"
        f"Expected correct answer: {expected_answer}\n"
        f"Student's actual response: {student_utterance}\n\n"
        "Evaluate the student's answer for conceptual correctness against the expected answer.\n"
        "CRITICAL RULES:\n"
        "- Ignore filler words (e.g., 'um', 'I think', 'maybe').\n"
        "- Focus strictly on whether the core concept matches.\n"
        "- If the transcript is totally garbled, completely incomplete, or ambiguous, return 'uncertain'.\n\n"
        "Reply with exactly one word: 'correct', 'incorrect', or 'uncertain'."
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
            temperature=0.0
        )
        verdict = response.choices[0].message.content.strip().lower()
        verdict = "".join(c for c in verdict if c.isalpha())
        
        # Groq Llama3 sometimes adds extra words like "the answer is correct". Let's handle that.
        if "correct" in verdict and "incorrect" not in verdict:
            return "correct"
        elif "incorrect" in verdict:
            return "incorrect"
        elif "uncertain" in verdict:
            return "uncertain"
            
        if verdict in ["correct", "incorrect", "uncertain"]:
            return verdict
        return "uncertain"
    except Exception as e:
        print(f"[check_answer_correctness] LLM call failed after retries: {e}")
        return "uncertain"
