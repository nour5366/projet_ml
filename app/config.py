"""Configuration : tout vient du fichier .env (jamais de secret dans le code)."""
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # lit .env s'il existe ; ne remplace pas une variable déjà définie

RACINE = Path(__file__).resolve().parent.parent
DATA_DIR = RACINE / "data"
RESULTATS_DIR = RACINE / "resultats"

MODE = os.getenv("INFERENCE_MODE", "mock").lower()   # "mock" ou "real"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "")
GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "4"))

def _parse_delais(valeur: str) -> list[float]:
    try:
        return [float(x.strip()) for x in valeur.split(",") if x.strip()]
    except Exception:
        return [1.0, 2.0, 4.0, 8.0]

GEMINI_BACKOFF_DELAYS: list[float] = _parse_delais(os.getenv("GEMINI_BACKOFF_DELAYS", "1.0, 2.0, 4.0, 8.0"))
MODEL_ID = os.getenv("MODEL_ID", "qwen/qwen3.8-27b")
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.60"))

SIMULER_PANNE = os.getenv("SIMULER_PANNE", "0") == "1"   # "1" : le mock plante (pour voir un 503)

MAX_TOURS = 5         # l'agent s'arrête après 5 tours (protège le quota)
PAUSE_GROQ = 2.1       # 30 requêtes/minute au maximum -> 2,1 s entre deux appels

# Date du jour FIXÉE : les résultats sont les mêmes pour tout le monde.
AUJOURDHUI = date(2026, 11, 15)

# ── Multimédia ────────────────────────────────────────────────────────────────
# Taille maximale : 5 Mo pour les images, 10 Mo pour les audios.
MAX_IMAGE_SIZE_BYTES: int = int(os.getenv("MAX_IMAGE_SIZE_BYTES", str(5 * 1024 * 1024)))   # 5 Mo
MAX_AUDIO_SIZE_BYTES: int = int(os.getenv("MAX_AUDIO_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10 Mo

# Types MIME acceptés (liste de référence ; la validation binaire reste obligatoire).
ALLOWED_IMAGE_MIME: set[str] = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_MIME: set[str] = {"audio/wav", "audio/x-wav", "audio/mpeg",
                                 "audio/mp4", "audio/ogg", "audio/x-m4a",
                                 "audio/mp3"}

# Signatures binaires (magic bytes) : les premiers octets d'un fichier révèlent son vrai format.
#   JPEG  : FF D8 FF
#   PNG   : 89 50 4E 47 0D 0A 1A 0A
#   WEBP  : 52 49 46 46 … 57 45 42 50 (RIFF…WEBP)
#   WAV   : 52 49 46 46 … 57 41 56 45 (RIFF…WAVE)
#   MP3   : FF FB / FF F3 / FF F2 / ID3
#   M4A   : 00 00 00 … 66 74 79 70 (ftyp atom)
#   OGG   : 4F 67 67 53 (OggS)
IMAGE_MAGIC: list[bytes] = [
    b"\xff\xd8\xff",          # JPEG
    b"\x89PNG\r\n\x1a\n",    # PNG
    b"RIFF",                  # WEBP (RIFF container – vérifié plus finement dans le code)
]
AUDIO_MAGIC: list[bytes] = [
    b"RIFF",                  # WAV (RIFF container – vérifié plus finement)
    b"\xff\xfb", b"\xff\xf3", b"\xff\xf2",   # MP3 (sans ID3)
    b"ID3",                   # MP3 avec tag ID3
    b"OggS",                  # OGG/Vorbis
]
# M4A : signature plus flexible détectée dans le validateur (atom ftyp à l'offset 4).
