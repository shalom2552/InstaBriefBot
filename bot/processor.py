from openai import OpenAI
from dotenv import load_dotenv
import os

GPT_MODEL="gpt-3.5-turbo"

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_keywords(question: str):
    prompt = f"""המשתמש שאל שאלה:
    "{question}"

    המטרה שלך היא לזהות את מילות המפתח המרכזיות בשאלה.

    החזר רק רשימת מילים בעברית, בפורמט פייתון תקני של רשימה. 
    לדוגמה: ['ביבי', 'שריפה', '2025-05-02']

    !אל תוסיף הסבר, כותרת או טקסט נוסף – רק את הרשימה בפורמט הזה.

    תוצאה:
    """


    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return eval(response.choices[0].message.content)

def summarize(question: str, messages: list):
    context = "\n".join(f"[{m['date']}] {m['text']}" for m in messages)
    prompt = f"""הודעות הטלגרם הבאות התקבלו ממקורות חדשותיים שונים:

    {context}

    בהתבסס על ההודעות האלו, ענה בצורה מקיפה ומעמיקה על השאלה:
    "{question}"

    המענה צריך לכלול:
    - מידע עדכני ורלוונטי
    - הסברים ופרשנויות לפי הצורך
    - תובנות על ההשלכות האפשריות
    - שימוש בתבליטים (•) במידה ויש מספר נקודות

    כתוב בעברית צחה, בגובה העיניים, אך בצורה רצינית וברורה.
    השתדל להפוך את המידע לעניין לקורא, לא רק רשימת כותרות.
    """
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
