import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("AI_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("AI_API_KEY", "ollama")
)

def query_ai(prompt: str, system_prompt: str = "You are a helpful assistant.", json_mode: bool = False) -> str:
    options = {}
    if json_mode:
        options["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL", "llama3.2:1b"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        **options,
    )
    return response.choices[0].message.content