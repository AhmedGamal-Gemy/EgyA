import os
import json
from typing import Literal
from litellm import acompletion
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import litellm
from shared.enums.flag_type import AudienceLevel

PacingVerdict = Literal["on_pace", "too_fast", "too_slow"]
ClarityVerdict = Literal["clear", "unclear_for_level"]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.ServiceUnavailableError))
)
async def _call_llm_with_retry(*args, **kwargs):
    return await acompletion(*args, **kwargs)

async def assess_pacing_clarity(
    transcript_line: str,
    audience_level: AudienceLevel,
) -> tuple[PacingVerdict, ClarityVerdict]:
    prompt = (
        f"You are evaluating instruction pacing and clarity for a {audience_level.value} audience based on a live class transcript.\n"
        f"Transcript excerpt: \"{transcript_line}\"\n\n"
        "Evaluate two factors:\n"
        "1. Pacing: Determine if the teacher is going 'too_fast', 'too_slow', or 'on_pace'. Only flag 'too_fast' or 'too_slow' if there is explicit feedback or obvious rushing/dragging.\n"
        "2. Clarity: Determine if the explanation is 'clear' or 'unclear_for_level'. Flag 'unclear_for_level' if there is unexplained jargon or explicit student complaints about clarity.\n\n"
        "Output ONLY valid JSON in this exact format, with no markdown formatting or extra text:\n"
        "{\"pacing\": \"<on_pace|too_fast|too_slow>\", \"clarity\": \"<clear|unclear_for_level>\"}"
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
        content = response.choices[0].message.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        # Groq Llama3 might output extra text, so we can try to extract just the json part
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        data = json.loads(content)
        pacing = data.get("pacing", "on_pace")
        clarity = data.get("clarity", "clear")
        
        if pacing not in ["on_pace", "too_fast", "too_slow"]:
            pacing = "on_pace"
        if clarity not in ["clear", "unclear_for_level"]:
            clarity = "clear"
            
        return pacing, clarity
    except Exception as e:
        print(f"[assess_pacing_clarity] LLM call failed or bad JSON: {e}")
        return "on_pace", "clear"
