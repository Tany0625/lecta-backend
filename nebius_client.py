import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NEBIUS_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("NEBIUS_API_KEY", "ollama")
)

def query_ai(prompt: str) -> str:
    response = client.chat.completions.create(
        model = os.getenv("MODEL_NAME", "llama3.2:1b"),
        messages = [
            {"role": "system", "content": "You are a helpful assistant for lecta."},
            {"role": "user", "content": prompt}
        ],
        temperature = 0.2
    )

    return response