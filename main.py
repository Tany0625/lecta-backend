import calendar
import json
import os
import re
import time
from collections import defaultdict, deque
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from ai_client import query_ai
from pdf_reader import extract_pdf_text
from prompts import NOTICE_ANALYSIS_PROMPT

# On the server we set HIDE_DOCS=1 so the public /docs test page is switched off.
HIDE_DOCS = os.getenv("HIDE_DOCS") == "1"
app = FastAPI(
    docs_url=None if HIDE_DOCS else "/docs",
    redoc_url=None,
    openapi_url=None if HIDE_DOCS else "/openapi.json",
)

# Limits for the cards. Change these numbers if your layout needs it.
TASK_MAX_CHARS = 35
SUMMARY_MAX_CHARS = 80
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB upload limit
# Rate limit: how many notices one user (one IP address) may send per hour.
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))
RATE_WINDOW = 3600  # seconds
recent_hits = defaultdict(deque)
MAX_ITEMS = 8

PRIORITIES = ["critical", "high", "medium", "low"]

# Fixed college rules, checked against the task name (whole words only)
CRITICAL_WORDS = re.compile(r"\b(?:exam|examination|viva|detention)s?\b")
HIGH_WORDS = re.compile(
    r"\b(?:assignment|project|record|file|report|test|presentation|submission|fee|quiz)(?:s|zes)?\b"
)


class NoticeRequest(BaseModel):
    text: str = Field(max_length=12000)
    source: str = "Pasted text"

def check_rate_limit(request: Request):
    """Stop one user from sending too many notices in an hour."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    if len(recent_hits) > 10000:  # safety: never let this list grow forever
        recent_hits.clear()

    hits = recent_hits[ip]
    while hits and now - hits[0] > RATE_WINDOW:
        hits.popleft()  # forget requests older than one hour
    if len(hits) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many uploads. Please try again in a while.")
    hits.append(now)

def shorten(text, limit):
    """Tidy extra spaces and cut the text at a word boundary if it is too long."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]  # drop the half-cut last word
    return cut.rstrip(" -,;:") + "…"


def clean_date(value):
    """Return the date only if it is a real YYYY-MM-DD date, otherwise None."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def date_is_in_text(iso_date, text):
    """True only if this date (YYYY-MM-DD) is really written in the text."""
    year, month, day = (int(part) for part in iso_date.split("-"))
    text = text.lower()

    # written with numbers, day first, like 5/12 or 05-12-2026
    if re.search(rf"(?<!\d)0?{day}\s*[/.-]\s*0?{month}(?!\d)", text):
        return True

    # written like "5 December" or "Dec 5": the day number AND the month name must appear
    day_found = re.search(rf"(?<!\d)0?{day}(?!\d)", text)
    month_found = calendar.month_name[month].lower()[:3] in text
    return bool(day_found and month_found)


def normalize_dates(text):
    """Rewrite dates like 05/12/2026 as '5 December 2026' so the AI cannot mix up day and month."""

    def rewrite(match):
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return match.group(0)  # not a real date, leave it alone
        if year < 100:
            year += 2000  # 26 means 2026
        return f"{day} {calendar.month_name[month]} {year}"

    return re.sub(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4}|\d{2})(?!\d)", rewrite, text)


def collapse_extended_range(start, end, text):
    """'Extended from X to Y' means one deadline (Y), not a range. Only applies when both dates
    are in the same sentence as the word 'extend'."""
    for sentence in re.split(r"[.!?\n]+", text):
        if "extend" in sentence.lower() and date_is_in_text(start, sentence) and date_is_in_text(end, sentence):
            return end, None
    return start, end


def decide_priority(task_name, ai_priority):
    """Use fixed college rules for obvious words, otherwise trust the AI."""
    name = task_name.lower()
    if CRITICAL_WORDS.search(name):
        return "critical"
    if HIGH_WORDS.search(name):
        return "high"
    return ai_priority if ai_priority in PRIORITIES else "medium"


def read_ai_json(raw):
    """Turn the AI's text into a Python dictionary, repairing small mistakes."""
    start = raw.find("{")
    end = raw.rfind("}")
    text = raw[start : end + 1] if end > start else raw[start:]
    # try the text as it is, then with closing brackets added (the AI sometimes forgets them)
    for ending in ["", "}", "]}", "}]}"]:
        try:
            return json.loads(text + ending)
        except json.JSONDecodeError:
            continue
    raise HTTPException(status_code=502, detail="The AI gave an unreadable answer. Please try again.")


def build_item(item, text, source):
    """Check one item from the AI and return the clean version, or None to skip it."""
    if not isinstance(item, dict):
        return None

    # the AI sometimes writes the word "null" in quotes; make it a real "nothing"
    item = {key: (None if value == "null" else value) for key, value in item.items()}

    # Nothing to do (news, changes, events): goes to the Notice Board
    if str(item.get("kind")).strip().lower() != "task":
        summary = item.get("summary")
        if not summary:
            return None
        return {"kind": "notice", "summary": f"{shorten(summary, SUMMARY_MAX_CHARS)} ({source})"}

    # Otherwise it is a task: check each part before sending it on
    start = clean_date(item.get("start_date"))
    end = clean_date(item.get("end_date"))

    # throw away any date that is not really written in the notice
    date_was_removed = False
    if start and not date_is_in_text(start, text):
        start, date_was_removed = None, True
    if end and not date_is_in_text(end, text):
        end, date_was_removed = None, True
    if end and (start is None or end <= start):
        end = None  # a bad range, or a "range" of one day
    if start and end:
        start, end = collapse_extended_range(start, end, text)

    task = shorten(item.get("task") or "Untitled task", TASK_MAX_CHARS)
    priority = decide_priority(task, str(item.get("priority")).strip().lower())

    # turn the AI's confidence into a whole number from 0 to 100
    try:
        confidence = float(str(item.get("confidence")).strip().rstrip("%"))
        if 0 < confidence <= 1:
            confidence = confidence * 100  # the AI wrote 0.9 instead of 90
        confidence = max(0, min(100, int(confidence)))
    except (ValueError, OverflowError):
        confidence = 0  # no usable number, so we trust nothing

    if date_was_removed:
        confidence = min(confidence, 60)  # the AI gave a date the notice does not contain
    if start is None:
        confidence = min(confidence, 70)  # no date, so never very sure
        if item.get("start_date"):
            confidence = min(confidence, 40)  # the AI gave a date, but it was wrong or invented

    return {
        "kind": "task",
        "task": task,
        "start_date": start,
        "end_date": end,
        "priority": priority,
        "confidence": confidence,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def process_notice(raw_text, source):
    """The shared pipeline: notice text in, clean items out. Used by both endpoints."""
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    prompt = NOTICE_ANALYSIS_PROMPT.replace("TODAY_DATE", today)
    text = normalize_dates(raw_text)

    try:
        raw = query_ai(text, prompt, json_mode=True)
    except Exception as error:
        print("AI request failed:", type(error).__name__)  # the error type only, never the notice text
        raise HTTPException(status_code=503, detail="The AI is busy right now. Please try again in a minute.")
    
    data = read_ai_json(raw)

    items = data.get("items")
    if not isinstance(items, list):
        items = [data]  # the AI forgot the "items" list and gave a single item directly

    results = []
    for item in items[:MAX_ITEMS]:
        result = build_item(item, text, source)
        if result and result not in results:
            results.append(result)

    if not results:
        results.append({"kind": "notice", "summary": f"No clear notice found. ({source})"})

    return {"items": results}


@app.post("/analyze", dependencies=[Depends(check_rate_limit)])
def analyze(request: NoticeRequest):
    return process_notice(request.text, request.source)


@app.post("/analyze-file", dependencies=[Depends(check_rate_limit)])
def analyze_file(file: UploadFile = File(...)):
    data = file.file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (max 10 MB).")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")
    try:
        text = extract_pdf_text(data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return process_notice(text, file.filename or "PDF")