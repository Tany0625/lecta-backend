import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=40.0, max_retries=1)

def query_ai(prompt: str, system_prompt: str = "You are a helpful assistant.", json_mode: bool = False) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    options = {
        "model": os.getenv("AI_MODEL", "openai/gpt-oss-20b"),
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 2048,
        "top_p": 1,
        "reasoning_effort": "medium",
    }

    if json_mode:
        options["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(**options)
    return completion.choices[0].message.content