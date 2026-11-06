import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai_client import query_ai
from prompts import NOTICE_ANALYSIS_PROMPT

app = FastAPI()

class NoticeRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(request: NoticeRequest):
    raw = query_ai(request.text, NOTICE_ANALYSIS_PROMPT)
    print("RAW AI ANSWER:", raw)
    start = raw.find("{")
    end = raw.rfind("}")

    if end < start:
        text = raw[start:] + "}"
    else:
        text = raw[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="The AI gave an unreadable answer. Please try again.")

    for key, value in data.items():
        if value == "null":
            data[key] = None

    return data