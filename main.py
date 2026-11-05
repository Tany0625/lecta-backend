from fastapi import FastAPI
from pydantic import BaseModel
from ai_client import query_ai

app = FastAPI()

class NoticeRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(request: NoticeRequest):
    result = query_ai(request.text)
    return {"result": result}