# Manual test script. Needs a real GROQ_API_KEY in .env. Run it with: python <this file>
import json
from fastapi import HTTPException
from main import analyze, NoticeRequest

NOTICES = [
    "Semester exams will be held from 25 November to 5 December 2026 for all ECE students.",
    "Friday's lecture is cancelled due to a college event.",
    "Physics practical record must be submitted by 20 November, 5 PM. Applies to ECE 1st year.",
    "Submit your Chemistry assignment soon. Details will follow.",
    "The annual cultural fest will be held on 12 December in the college auditorium.",
    "Please fill the semester feedback form by 30 November.",
    "Mid-sem practical exams: 05/12/2026 to 09/12/2026. Carry your lab file and ID card.",
    "Fee payment last date is extended from 10 November to 17 November 2026.",
    "Aaj ka class cancel hai. Kal tak Maths assignment submit karna hai.",
    "hi",
]

for number, text in enumerate(NOTICES, start=1):
    print(f"\n--- Test {number} ---")
    print("Notice:", text)
    try:
        result = analyze(NoticeRequest(text=text))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except HTTPException as error:
        print("ERROR:", error.detail)