from google import genai
from app.config import GEMINI_API_KEY, GEMINI_MODEL

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    r = client.models.generate_content(model=GEMINI_MODEL, contents="Réponds juste: OK")
    print("✅ CLÉ VALIDE :", r.text)
except Exception as e:
    print("❌ ERREUR :", str(e)[:200])
