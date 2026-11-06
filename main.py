import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_client import query_ai
from prompts import NOTICE_ANALYSIS_PROMPT

app = FastAPI()
TASK_MAX_CHARS = 35
SUMMARY_MAX_CHARS = 80

PRIORITIES = ["critical","high","medium","low"]

class NoticeRequest(BaseModel):
    text: str
    source: str = "Pasted Text"

def shorten(text, limit):
    """Tidy extra spaces and cut the text if it is longer than the limit."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"

def clean_date(value):
    """Return the date only if it is a real YYYY-MM-DD date, otherwise None."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None

def read_ai_json(raw):
    """Turn the AI's text into a Python dictionary, repairing small mistakes."""
    start = raw.find("{")
    end = raw.rfind("}")
    if end < start:
        text = raw[start:] + "}"
    else:
        text = raw[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="The AI gave an unreadable answer. Please try again.")
    for key, value in data.items():
        if value == "null":
            data[key] = None
        return data

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: NoticeRequest):
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    prompt = NOTICE_ANALYSIS_PROMPT.replace("TODAY_DATE", today)

    raw = query_ai(request.text, prompt, json_mode=True)
    print("RAW AI ANSWER:", raw)
    data = read_ai_json(raw)

    if str(data.get("kind")).strip().lower() != "task":
        summary = shorten(data.get("summary") or request.text, SUMMARY_MAX_CHARS)
        return {"kind": "notice", "summary": f"{summary} ({request.source})"}

    start = clean_date(data.get("start_date"))
    end = clean_date(data.get("end_date"))
    if end and (start is None or end <= start):
        end = None  

    priority = str(data.get("priority")).strip().lower()
    if priority not in PRIORITIES:
        priority = "medium"

    try:
        confidence = float(str(data.get("confidence")).strip().rstrip("%"))
        if 0 < confidence <= 1:
            confidence = confidence * 100  
        confidence = max(0, min(100, int(confidence)))
    except (ValueError, OverflowError):
        confidence = 0  

    if start is None:
        confidence = min(confidence, 70)  
    if data.get("start_date") and start is None:
        confidence = min(confidence, 30)  

    return {
        "kind": "task",
        "task": shorten(data.get("task") or "Untitled task", TASK_MAX_CHARS),
        "start_date": start,
        "end_date": end,
        "priority": priority,
        "confidence": confidence,
    }