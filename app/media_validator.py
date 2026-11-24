"""Validation des fichiers multimédia (images et audios).

Stratégie en 4 étapes, dans l'ordre :
  1. Taille   → HTTP 413 si dépassée
  2. MIME     → HTTP 415 si non autorisé
  3. Magic    → HTTP 415 si les octets de signature ne correspondent à aucun format connu
  4. Décodage → HTTP 415 si le fichier est corrompu (Pillow ou pydub refusent de l'ouvrir)

Pourquoi ne pas se contenter du MIME ?
  Un attaquant (ou un bug) peut envoyer un fichier .exe avec Content-Type: image/jpeg.
  Seuls les magic bytes et le décodage réel permettent de détecter ce type de fraude.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import HTTPException, UploadFile

from app.config import (
    ALLOWED_AUDIO_MIME,
    ALLOWED_IMAGE_MIME,
    AUDIO_MAGIC,
    IMAGE_MAGIC,
    MAX_AUDIO_SIZE_BYTES,
    MAX_IMAGE_SIZE_BYTES,
)
from app.schemas import AudioFormat, ImageFormat, MediaType, MediaValidationResult

journal = logging.getLogger("uvicorn.error")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _correspond_magic(donnees: bytes, magic_list: list[bytes]) -> bool:
    """Vérifie que les premiers octets du fichier correspondent à l'une des signatures connues."""
    for magic in magic_list:
        if donnees[:len(magic)] == magic:
            return True
    return False


def _est_webp(donnees: bytes) -> bool:
    """WEBP = container RIFF avec le marqueur 'WEBP' aux octets 8-12."""
    return (len(donnees) >= 12
            and donnees[:4] == b"RIFF"
            and donnees[8:12] == b"WEBP")


def _est_wav(donnees: bytes) -> bool:
    """WAV = container RIFF avec le marqueur 'WAVE' aux octets 8-12."""
    return (len(donnees) >= 12
            and donnees[:4] == b"RIFF"
            and donnees[8:12] == b"WAVE")


def _est_m4a(donnees: bytes) -> bool:
    """M4A = atom MP4/ftyp. L'atome 'ftyp' commence généralement à l'offset 4."""
    return len(donnees) >= 8 and donnees[4:8] == b"ftyp"


def _detecter_format_image(donnees: bytes) -> Optional[str]:
    """Retourne 'jpeg', 'png' ou 'webp', ou None si non reconnu."""
    if donnees[:3] == b"\xff\xd8\xff":
        return ImageFormat.jpeg
    if donnees[:8] == b"\x89PNG\r\n\x1a\n":
        return ImageFormat.png
    if _est_webp(donnees):
        return ImageFormat.webp
    return None


def _detecter_format_audio(donnees: bytes) -> Optional[str]:
    """Retourne 'wav', 'mp3', 'm4a' ou 'ogg', ou None si non reconnu."""
    if _est_wav(donnees):
        return AudioFormat.wav
    if _est_m4a(donnees):
        return AudioFormat.m4a
    if donnees[:3] == b"ID3" or donnees[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return AudioFormat.mp3
    if donnees[:4] == b"OggS":
        return AudioFormat.ogg
    return None


# ── Validation image ──────────────────────────────────────────────────────────

async def valider_image(fichier: UploadFile) -> MediaValidationResult:
    """
    Valide une image uploadée.
    Lève une HTTPException (413 ou 415) si la validation échoue.
    Retourne un MediaValidationResult si tout est correct.
    """
    # 1. Taille — on lit tout en mémoire une seule fois
    donnees = await fichier.read()
    taille = len(donnees)

    if taille == 0:
        raise HTTPException(
            status_code=415,
            detail="Le fichier est vide.",
        )

    if taille > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Image trop grande : {taille} octets reçus, "
                f"maximum autorisé {MAX_IMAGE_SIZE_BYTES} octets "
                f"({MAX_IMAGE_SIZE_BYTES // (1024*1024)} Mo)."
            ),
        )

    # 2. MIME déclaré par le client
    content_type = (fichier.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Type MIME non supporté : '{content_type}'. "
                f"Types acceptés : {', '.join(sorted(ALLOWED_IMAGE_MIME))}."
            ),
        )

    # 3. Signature binaire (magic bytes)
    format_detecte = _detecter_format_image(donnees)
    if format_detecte is None:
        raise HTTPException(
            status_code=415,
            detail=(
                "Le contenu binaire du fichier ne correspond à aucun format image connu "
                "(JPEG, PNG, WEBP). Le fichier pourrait être corrompu ou déguisé."
            ),
        )

    # 4. Décodage réel avec Pillow
    # On utilise load() plutôt que verify() car verify() ferme le fichier après l'appel
    # et est trop strict sur les JPEG légèrement incomplets (terminaison sans EOI).
    try:
        from PIL import Image  # import local → pas de crash si absent
        img = Image.open(io.BytesIO(donnees))
        img.load()   # force le décodage complet des pixels
    except ImportError:
        journal.warning("Pillow non installé – décodage image ignoré.")
    except Exception as exc:
        raise HTTPException(
            status_code=415,
            detail=f"Le fichier image ne peut pas être décodé : {exc}",
        ) from exc

    return MediaValidationResult(
        valide=True,
        media_type=MediaType.image,
        format_detecte=format_detecte,
        taille_octets=taille,
    )


# ── Validation audio ──────────────────────────────────────────────────────────

async def valider_audio(fichier: UploadFile) -> tuple[MediaValidationResult, bytes]:
    """
    Valide un fichier audio uploadé.
    Lève une HTTPException (413 ou 415) si la validation échoue.
    Retourne (MediaValidationResult, donnees_brutes) pour éviter une double lecture.
    """
    donnees = await fichier.read()
    taille = len(donnees)

    if taille == 0:
        raise HTTPException(status_code=415, detail="Le fichier est vide.")

    if taille > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Audio trop grand : {taille} octets reçus, "
                f"maximum autorisé {MAX_AUDIO_SIZE_BYTES} octets "
                f"({MAX_AUDIO_SIZE_BYTES // (1024*1024)} Mo)."
            ),
        )

    # MIME
    content_type = (fichier.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_AUDIO_MIME:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Type MIME audio non supporté : '{content_type}'. "
                f"Types acceptés : {', '.join(sorted(ALLOWED_AUDIO_MIME))}."
            ),
        )

    # Magic bytes
    format_detecte = _detecter_format_audio(donnees)
    if format_detecte is None:
        raise HTTPException(
            status_code=415,
            detail=(
                "Le contenu binaire du fichier ne correspond à aucun format audio connu "
                "(WAV, MP3, M4A, OGG). Le fichier pourrait être corrompu ou déguisé."
            ),
        )

    # Décodage réel (pydub + ffmpeg)
    try:
        from pydub import AudioSegment  # import local → pas de crash si absent
        from pydub.exceptions import CouldntDecodeError

        AudioSegment.from_file(io.BytesIO(donnees))
    except ImportError:
        journal.warning("pydub non installé – décodage audio ignoré.")
    except Exception as exc:
        raise HTTPException(
            status_code=415,
            detail=f"Le fichier audio ne peut pas être décodé : {exc}",
        ) from exc

    resultat = MediaValidationResult(
        valide=True,
        media_type=MediaType.audio,
        format_detecte=format_detecte,
        taille_octets=taille,
    )
    return resultat, donnees
