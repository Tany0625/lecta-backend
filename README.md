# Lecta Backend

FastAPI backend for **[Lecta](https://github.com/Tany0625/Lecta)**, an Android app that turns college notices into tasks. It receives a notice (PDF or text), reads it with an AI model, and returns structured tasks and notices.

## How it works

```text
PDF upload → text extraction (pypdf) → AI model (Groq) → validation and cleanup → JSON
```

The AI's answer is not trusted blindly. The backend checks every date against the notice text, applies fixed priority rules (exams are always critical), limits task name length, and lowers the confidence score when something looks guessed.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Check that the server is running |
| POST | `/analyze` | Send notice text as JSON: `{"text": "...", "source": "..."}` |
| POST | `/analyze-file` | Upload a PDF notice (multipart field name: `file`) |

Response:

```json
{
  "items": [
    {"kind": "task", "task": "Engineering Maths internal exam", "start_date": "2026-12-05",
     "end_date": null, "priority": "critical", "confidence": 95},
    {"kind": "notice", "summary": "Monday's Electronics Lab shifted to Tuesday. (notice.pdf)"}
  ]
}
```

- `kind: "task"` means the student has to do something. It has dates, a priority (`critical`, `high`, `medium`, `low`) and a confidence score from 0 to 100.
- `kind: "notice"` means information only, such as a cancelled class.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your real key in .env
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the endpoints in the browser.

## Environment variables

| Name | Required | Meaning |
|---|---|---|
| `GROQ_API_KEY` | yes | Your Groq API key |
| `AI_MODEL` | no | Model name (default: `openai/gpt-oss-20b`) |
| `RATE_LIMIT_PER_HOUR` | no | Notices allowed per user per hour (default: 10) |
| `HIDE_DOCS` | no | Set to `1` on a public server to turn off `/docs` |

Never commit your `.env` file.

## Deploying

Build command: `pip install -r requirements.txt`

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
```

The proxy flags make the rate limit see each user's real IP address instead of the hosting provider's.

## Limits

- PDFs must contain real text. Scanned PDFs and images are not supported yet.
- Maximum 10 MB per file; only the first 10 pages and about 12,000 characters are read.
- 10 notices per hour per user (adjustable).
- On free hosting, the first request after a quiet period can take up to a minute.

## Privacy

Notice text is sent to the AI provider (Groq) to be analysed. The backend does not store uploaded files or notice text, and its logs record only error types.

## Manual tests

`test_ai.py`, `test_notices.py` and `test_long.py` are manual scripts that run sample notices through the AI. They need a real `GROQ_API_KEY` in `.env`.

## License

MIT