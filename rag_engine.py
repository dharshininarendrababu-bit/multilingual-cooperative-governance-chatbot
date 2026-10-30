import json
import os
import google.generativeai as genai

DATA_FILE = "data.json"

def get_fallback_answer(query):
    # Unga data.json file-la irundhu simple match
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    q = item.get("question", "").lower()
                    if any(word in q for word in query.lower().split()):
                        return item.get("answer", "")
        except Exception:
            pass
    return "Cooperative Society Services: Information on PACS, KCC Loan (4% interest) & PMFBY Crop Insurance."

def query_legal_rag(user_query, language="English", api_key=None):
    # 1. Gemini API key irundhaa AI response tharum
    if api_key and api_key.strip():
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            You are a helpful Indian Cooperative Society and Legal assistant.
            Language to reply: {language}
            User Question: {user_query}
            
            Provide a helpful, clear, and rural-friendly answer in {language}.
            """
            resp = model.generate_content(prompt)
            return resp.text
        except Exception as e:
            print("Gemini API error:", e)

    # 2. Key illana unga data.json la irundhu default answer
    return get_fallback_answer(user_query)