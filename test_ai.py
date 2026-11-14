# Manual test script. Needs a real GROQ_API_KEY in .env. Run it with: python <this file>
from ai_client import query_ai

if __name__ == "__main__":
    print("Sending prompt to local AI model...")
    prompt_text = "Summarize this in one short sentence: 'Math assignment 3 is due on Friday October 16th at 11:59 PM."

    response = query_ai(prompt_text)
    print("Response from AI model:")
    print(response)