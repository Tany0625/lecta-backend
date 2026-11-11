import json
from fastapi import HTTPException
from main import analyze, NoticeRequest

NOTICES = [
    """XYZ INSTITUTE OF TECHNOLOGY
Office of the Controller of Examinations

NOTICE: END SEMESTER EXAMINATIONS (ODD SEMESTER 2026-27)

All B.Tech students are informed that the End Semester Examinations will begin on 8 December 2026 and end on 22 December 2026. The detailed date sheet will be put up on the notice board on 25 November 2026.

All students must fill the online examination form on the ERP portal on or before 28 November 2026. Forms submitted after this date will be accepted up to 2 December 2026 with a late fee of Rs. 500.

Students with less than 75% attendance will not be permitted to appear in the examination. Such students should meet their Head of Department before 30 November 2026 with a written request.

Admit cards will be available on the ERP portal from 4 December 2026.

Controller of Examinations""",

    """Good morning everyone 🙏

Important updates for today:

1. Tomorrow's DSA lab is cancelled. It will be taken on Saturday at the same time.
2. Physics practical file to be submitted to Ma'am by 14th November. No extension will be given.
3. Maths Assignment 3 (Q1 to Q10, Unit 2) - last date 18/11/2026.
4. Those who have not paid the bus fee, please pay at the accounts office by Friday.

Regards,
CR, ECE-A""",

    """Dear students,

The Training & Placement Cell is organising a Resume Building Workshop on 20 November 2026 from 2 PM to 4 PM in Seminar Hall 2. Attendance is mandatory for all final year students.

Pre-registration for the Google Cloud Study Jam is open till 17 November 2026 for all interested students.

The annual tech fest TechNova will be held on 5 and 6 December 2026. Students who wish to volunteer can give their names to the coordinators.

Students who have not yet submitted their NPTEL certificates must do so at the T&P office before 25 November 2026.

Regards,
T&P Cell""",

    """NOTICE

The college will remain closed from 14 November to 16 November 2026 on account of the festival break. Regular classes will resume on 17 November 2026.

The Basic Electronics internal test, which was scheduled for 18 November 2026, stands postponed. The new date will be informed later.

All students are advised to submit their pending Chemistry lab records to the department office within the first week after the college reopens.

Principal""",

    """*Forwarded many times*

Hello sabhi students 🙏 Mam ne bola hai ki Digital Electronics ka Assignment 2 ab 21 November tak jama karna hai (pehle 15 Nov tha, extended). Group projects ki presentation 24-26 November ke beech hogi, apni team ke saath slot book kar lo Google sheet me jaldi se. Jinko lab record sign karwana hai wo Friday ko 3rd floor lab me aaye. Koi problem ho to contact kar lena: 98XXXXXXXX. Thank you!! 🙏🙏""",
]

for number, text in enumerate(NOTICES, start=1):
    print(f"\n--- Long test {number} ---")
    print("Notice:", text[:70].replace("\n", " "), "...")
    try:
        result = analyze(NoticeRequest(text=text))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except HTTPException as error:
        print("ERROR:", error.detail)