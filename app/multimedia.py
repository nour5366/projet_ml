"""Routes FastAPI pour le bonus multimédia.

Endpoints :
  POST /multimedia/upload-image  → reçoit une image, la valide et l'analyse
  POST /multimedia/upload-audio  → reçoit un audio, le valide et l'analyse

Les deux routes renvoient un MediaAnalysisResult (texte extrait + métadonnées).
En cas d'erreur de validation, elles renvoient 413 ou 415 (jamais 500).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.media_analyzer import analyser_media
from app.media_validator import valider_audio, valider_image
from app.schemas import MediaAnalysisResult, MediaType

routeur = APIRouter(prefix="/multimedia", tags=["multimedia"])
journal = logging.getLogger("uvicorn.error")


@routeur.post(
    "/upload-image",
    response_model=MediaAnalysisResult,
    summary="Téléverser et analyser une image",
    description=(
        "Accepte une image JPEG, PNG ou WEBP (≤ 5 Mo). "
        "Renvoie une description du contenu visuel. "
        "Erreur 413 si trop grande, 415 si format non supporté ou fichier corrompu."
    ),
    responses={
        413: {"description": "Image trop grande (> 5 Mo)"},
        415: {"description": "Format non supporté ou fichier corrompu"},
    },
)
async def upload_image(
    fichier: UploadFile = File(..., description="Image JPEG, PNG ou WEBP à analyser"),
) -> MediaAnalysisResult:
    """
    1. Valide la taille, le MIME, les magic bytes et le décodage (Pillow).
    2. Analyse le contenu avec Gemini (mode réel) ou le simulateur (mode mock).
    3. Renvoie le texte extrait et les métadonnées.
    """
    # Validation — peut lever 413 ou 415
    validation = await valider_image(fichier)

    # Lecture des données (déjà lues dans le validateur via fichier.read() interne,
    # mais UploadFile ne garde pas le pointeur : on doit le remettre à zéro)
    await fichier.seek(0)
    donnees = await fichier.read()

    try:
        resultat = await analyser_media(
            donnees=donnees,
            media_type=MediaType.image,
            format_detecte=validation.format_detecte,
        )
    except HTTPException:
        raise
    except Exception as exc:
        journal.error("Erreur d'analyse image : %r", exc)
        raise HTTPException(
            status_code=503,
            detail="Service d'analyse multimédia temporairement indisponible.",
        ) from exc

    return resultat


@routeur.post(
    "/upload-audio",
    response_model=MediaAnalysisResult,
    summary="Téléverser et analyser un fichier audio",
    description=(
        "Accepte un fichier WAV, MP3, M4A ou OGG (≤ 10 Mo). "
        "Renvoie une transcription ou une description du contenu audio. "
        "Erreur 413 si trop grand, 415 si format non supporté ou fichier corrompu."
    ),
    responses={
        413: {"description": "Fichier audio trop grand (> 10 Mo)"},
        415: {"description": "Format non supporté ou fichier corrompu"},
    },
)
async def upload_audio(
    fichier: UploadFile = File(..., description="Audio WAV, MP3, M4A ou OGG à transcrire"),
) -> MediaAnalysisResult:
    """
    1. Valide la taille, le MIME, les magic bytes et le décodage (pydub).
    2. Analyse / transcrit le contenu avec Gemini (mode réel) ou le simulateur.
    3. Renvoie la transcription et les métadonnées.
    """
    # Validation — peut lever 413 ou 415
    # valider_audio retourne aussi les données brutes pour éviter une double lecture
    validation, donnees = await valider_audio(fichier)

    try:
        resultat = await analyser_media(
            donnees=donnees,
            media_type=MediaType.audio,
            format_detecte=validation.format_detecte,
        )
    except HTTPException:
        raise
    except Exception as exc:
        journal.error("Erreur d'analyse audio : %r", exc)
        raise HTTPException(
            status_code=503,
            detail="Service d'analyse multimédia temporairement indisponible.",
        ) from exc

    return resultat
