import os
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

async def detect_confusion(transcript_line: str) -> bool:
    prompt = (
        "You are evaluating a student's statement from a live class transcript.\n"
        "Your task is to detect if the student is genuinely confused, lost, fundamentally misunderstanding, or asking the teacher to repeat a basic concept.\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT flag mere hesitation (e.g., 'Um', 'I think').\n"
        "- Do NOT flag incorrect answers as confusion unless they explicitly state they are lost.\n"
        "- Do NOT flag advanced clarifying questions that show engagement rather than being lost.\n\n"
        f"Transcript: \"{transcript_line}\"\n\n"
        "Reply with exactly one word: 'yes' (if confused) or 'no' (if not confused)."
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
        return verdict == "yes"
    except Exception as e:
        print(f"[detect_confusion] LLM call failed after retries: {e}")
        return False
