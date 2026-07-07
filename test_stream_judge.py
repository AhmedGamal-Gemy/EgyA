import asyncio
import os
import re

# Load .env manually for testing
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

from shared.enums.flag_type import AudienceLevel
from services.stream_judge.tools.detect_confusion import detect_confusion
from services.stream_judge.tools.check_answer_correctness import check_answer_correctness
from services.stream_judge.tools.assess_pacing_clarity import assess_pacing_clarity

TRANSCRIPT_CHUNKS = [
    {
        "speaker": "Teacher",
        "text": "Alright everyone, welcome back. Today we're diving into the Keras Functional API. We use this when we need to build complex networks, like those with multiple inputs or outputs. Can anyone remind me what we use if the network is just a simple, straight line of layers?"
    },
    {
        "speaker": "Student 1",
        "text": "Um... is it the Sequential API?"
    },
    {
        "speaker": "Teacher",
        "text": "Exactly! Spot on. The Sequential API is for simple stacks. But look at my screen now. We define the Input first, and then we pass it to a Dense layer as if we are calling a function."
    },
    {
        "speaker": "Student 2",
        "text": "Wait a second, I am a bit lost here. Why do we put the (inputs) at the very end of the Dense layer line? I do not get this syntax at all."
    },
    {
        "speaker": "Teacher",
        "text": "Great question! That's exactly why it's called the Functional API. In Python, the layer instance acts as a callable here. Now, let me quickly show you how to do manual backpropagation using GradientTape... we write this line, then this one, calculate the gradients, apply them, and boom we are done! Let's move on to Convolutional Networks..."
    },
    {
        "speaker": "Student 1",
        "text": "Whoa, what was that speed! I completely missed everything you just did with GradientTape. Can you slow down?"
    },
    {
        "speaker": "Teacher",
        "text": "Oh, my apologies! I definitely rushed that. Let's step back. Before we go to CNNs, what is the default optimizer we usually use when compiling our Keras models for basic classification?"
    },
    {
        "speaker": "Student 3",
        "text": "I think it is the mean squared error optimizer."
    }
]

QUIZ_QUESTIONS = {
    "Can anyone remind me what we use if the network is just a simple, straight line of layers?": "Sequential API",
    "what is the default optimizer we usually use when compiling our Keras models for basic classification?": "Adam optimizer"
}

async def run_tests():
    print("==================================================")
    print("Testing Stream Judge Tools with Realistic Keras Data (GROQ Llama3)")
    print("==================================================\n")
    
    audience = AudienceLevel.ADULTS
    current_question_context = None
    expected_answer_context = None

    for i, chunk in enumerate(TRANSCRIPT_CHUNKS):
        speaker = chunk["speaker"]
        text = chunk["text"]
        print(f"[{speaker}]: {text}")
        
        if speaker == "Teacher":
            for q, a in QUIZ_QUESTIONS.items():
                if q.lower() in text.lower():
                    current_question_context = q
                    expected_answer_context = a
                    print(f"   -> [System Note] Teacher asked a known question. Awaiting student answer.")
                    break
        
        elif speaker.startswith("Student"):
            # Groq is super fast and has high rate limits (30 RPM for Llama3-8b), so 1.5s sleep is enough
            await asyncio.sleep(1.5) 
            is_confused = await detect_confusion(text)
            if is_confused:
                print(f"   [!] FLAG DETECTED: CONFUSION -> \"{text}\"")
                
            await asyncio.sleep(1.5)
            pacing, clarity = await assess_pacing_clarity(text, audience)
            if pacing == "too_fast":
                print(f"   [!] FLAG DETECTED: PACING (TOO FAST) -> based on student feedback")
            elif pacing == "too_slow":
                print(f"   [!] FLAG DETECTED: PACING (TOO SLOW)")
            if clarity == "unclear_for_level":
                print(f"   [!] FLAG DETECTED: CLARITY (UNCLEAR) -> based on student feedback")
            
            if current_question_context:
                await asyncio.sleep(1.5)
                verdict = await check_answer_correctness(
                    question=current_question_context,
                    expected_answer=expected_answer_context,
                    student_utterance=text
                )
                print(f"   -> ANSWER EVALUATION: '{verdict.upper()}' (Expected: {expected_answer_context})")
                
                if verdict == "incorrect":
                    print(f"   [!] FLAG DETECTED: WRONG_ANSWER")
                    
                current_question_context = None
                expected_answer_context = None
                
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())
