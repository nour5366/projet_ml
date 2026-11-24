import asyncio
import os
import sys
from pathlib import Path

# Ajouter la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import GEMINI_API_KEY, GEMINI_MODEL, MODE
from app.media_analyzer import analyser_media
from app.schemas import MediaType

async def tester():
    print(f"MODE: {MODE}")
    print(f"GEMINI_MODEL: {GEMINI_MODEL}")
    cle_masquee = (GEMINI_API_KEY[:4] + "..." + GEMINI_API_KEY[-4:]) if len(GEMINI_API_KEY) > 8 else "***"
    print(f"GEMINI_API_KEY (masquée, longueur {len(GEMINI_API_KEY)}): {cle_masquee}")
    
    # Données image JPEG minimales valides
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()
    
    try:
        res = await analyser_media(data, MediaType.image, "jpeg")
        print("✅ SUCCÈS APPEL RÉEL :", res)
    except Exception as e:
        print("❌ ÉCHEC APPEL RÉEL :", type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(tester())
