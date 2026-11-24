"""Analyse du contenu multimédia (images et audios).

Deux modes distincts et étanches :
  • mode "real"  → appelle réellement l'API Gemini multimodale avec les véritables octets de l'image.
                   Ne replie JAMAIS silencieusement sur une réponse prédéfinie en cas d'erreur.
  • mode "mock" / "simule" → simulation transparente et déterministe, clairement identifiée comme telle.
                   N'invente aucune fausse information (pas de marathon codé en dur).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import logging
from typing import Optional, Tuple

from fastapi import HTTPException
import httpx

from app.config import (
    GEMINI_API_KEY,
    GEMINI_BACKOFF_DELAYS,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    MODE,
)
from app.schemas import AudioFormat, ImageFormat, MediaAnalysisResult, MediaType

journal = logging.getLogger("uvicorn.error")

# ── Mode Simulé (MOCK) ────────────────────────────────────────────────────────

def _analyser_simule(donnees: bytes, media_type: MediaType, format_detecte: str) -> MediaAnalysisResult:
    """
    Génère une réponse de simulation pour le mode MOCK.
    Inspecte les caractéristiques réelles du fichier (dimensions, taille, empreinte)
    sans jamais inventer d'analyse textuelle factice ni prétendre qu'il s'agit d'un marathon.
    """
    taille_octets = len(donnees)
    empreinte = hashlib.sha256(donnees).hexdigest()[:12]

    if media_type == MediaType.image:
        largeur, hauteur = 0, 0
        mode_couleur = "inconnu"
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(donnees))
            largeur, hauteur = img.size
            mode_couleur = img.mode
        except Exception as exc:
            journal.warning("Impossible d'extraire les dimensions de l'image simulée : %r", exc)

        texte = (
            f"[SIMULATION – MODE MOCK ACTIF]\n"
            f"Le système fonctionne actuellement en mode simulé (INFERENCE_MODE=mock). "
            f"Aucun modèle d'IA multimodal n'a été appelé.\n\n"
            f"Propriétés techniques réelles du fichier image analysé :\n"
            f"• Format binaire : {format_detecte.upper()}\n"
            f"• Dimensions : {largeur} × {hauteur} pixels\n"
            f"• Espace colorimétrique : {mode_couleur}\n"
            f"• Taille des données : {taille_octets} octets ({taille_octets / 1024:.1f} Ko)\n"
            f"• Empreinte SHA-256 : {empreinte}\n\n"
            f"⚠️ En mode MOCK, aucune extraction sémantique "
            f"(sport, nom d'événement, date, lieu, horaires, inscriptions) n'est exécutée "
            f"afin de ne pas inventer d'informations absentes.\n"
            f"👉 Pour activer l'analyse visuelle réelle avec Gemini Vision, "
            f"renseignez GEMINI_API_KEY dans votre fichier .env et passez INFERENCE_MODE=real."
        )
    else:
        texte = (
            f"[SIMULATION – MODE MOCK ACTIF]\n"
            f"Fichier audio {format_detecte.upper()} reçu et validé ({taille_octets} octets, hash {empreinte}).\n"
            f"En mode MOCK, aucune transcription par IA n'est effectuée afin d'éviter toute invention.\n"
            f"👉 Pour transcrire réellement ce contenu audio, activez INFERENCE_MODE=real avec GEMINI_API_KEY."
        )

    return MediaAnalysisResult(
        media_type=media_type,
        format_detecte=format_detecte,
        taille_octets=taille_octets,
        texte_extrait=texte,
        confiance=1.0,
        mode="simule",
        metadata={
            "simulation": True,
            "mode": "mock",
            "sha256": empreinte,
        },
    )


# ── Mode Réel (Gemini Vision Multimodal) ──────────────────────────────────────

def _mime_pour_gemini(media_type: MediaType, format_detecte: str) -> str:
    """Convertit le format interne en type MIME standard pour l'API Gemini."""
    table_image = {
        ImageFormat.jpeg: "image/jpeg",
        ImageFormat.png: "image/png",
        ImageFormat.webp: "image/webp",
    }
    table_audio = {
        AudioFormat.wav: "audio/wav",
        AudioFormat.mp3: "audio/mp3",
        AudioFormat.m4a: "audio/mp4",
        AudioFormat.ogg: "audio/ogg",
    }
    if media_type == MediaType.image:
        return table_image.get(format_detecte, "image/jpeg")
    return table_audio.get(format_detecte, "audio/wav")


def _prompt_pour(media_type: MediaType) -> str:
    """Construit un prompt d'extraction strict et structuré selon le type de média."""
    if media_type == MediaType.image:
        return (
            "Tu es un assistant expert pour la plateforme SportsAI, spécialisé dans l'analyse d'affiches et de documents sportifs.\n"
            "Analyse minutieusement cette image et extrait uniquement les informations réellement et explicitement visibles.\n"
            "Structure impérativement ta réponse avec les rubriques suivantes :\n"
            "• Sport : [Nom du sport ou de la discipline représentée, ou 'Aucun (image sans rapport avec le sport)' si non sportif]\n"
            "• Événement : [Nom précis de l'événement, du tournoi ou de la compétition, ou 'Non mentionné']\n"
            "• Date : [Date(s), jour, mois, année ou période indiquée, ou 'Non mentionné']\n"
            "• Lieu : [Ville, stade, gymnase, adresse ou localisation, ou 'Non mentionné']\n"
            "• Horaires : [Heures de début/fin, créneaux ou programme horaire, ou 'Non mentionné']\n"
            "• Inscriptions : [Modalités, tarifs, date limite, site web ou contact pour s'inscrire, ou 'Non mentionné']\n"
            "• Texte visible & Description : [Transcription fidèle des principaux textes visibles et brève description de l'image]\n\n"
            "CONSIGNES STRICTES D'INTÉGRITÉ :\n"
            "- N'INVENTE JAMAIS d'information absente ou incertaine. Si une mention n'apparaît pas sur l'image, écris exactement 'Non mentionné'.\n"
            "- Si l'image n'a AUCUN RAPPORT avec le sport (ex. paysage, objet, document administratif, animal, etc.), "
            "indique clairement 'Cette image ne concerne pas un événement sportif' et décris ce qui est réellement visible.\n"
            "- Si l'image contient PEU OU PAS DE TEXTE, décris fidèlement les éléments visuels observés et précise explicitement 'Aucun texte visible'."
        )
    return (
        "Tu es un assistant de la plateforme SportsAI. "
        "Transcris fidèlement ce message audio en français, "
        "puis résume le sport mentionné et l'intention (inscription, information, autre). "
        "Si l'audio est inaudible ou sans rapport avec le sport, indique-le clairement."
    )


async def _appeler_gemini_endpoint(
    client: httpx.AsyncClient,
    modele: str,
    cle: str,
    corps: dict,
    delais: Optional[list[float]] = None,
    max_retries: Optional[int] = None,
) -> Tuple[Optional[dict], Optional[HTTPException]]:
    """
    Exécute un appel HTTP vers le modèle Gemini avec retry automatique et exponential backoff.

    Comportement :
      - Délais par défaut : 1s, 2s, 4s, 8s (GEMINI_BACKOFF_DELAYS).
      - Tentatives de réessai limitées à 4 maximum (GEMINI_MAX_RETRIES).
      - Erreurs avec réessai : HTTP 503, 502, 500, 429, timeouts et erreurs de connexion réseau.
      - Erreurs sans réessai (immédiates) : HTTP 400, 401, 403 (authentification/requête) et 404 (modèle non trouvé).
      - Règle 503 : Ne JAMAIS qualifier une indisponibilité (503) d'erreur de clé API.
    """
    if delais is None:
        delais = GEMINI_BACKOFF_DELAYS
    if max_retries is None:
        max_retries = GEMINI_MAX_RETRIES

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
    derniere_erreur: Optional[HTTPException] = None

    for tentative in range(max_retries + 1):
        delai = delais[tentative] if tentative < len(delais) else (delais[-1] if delais else 1.0)
        est_dernier_essai = (tentative >= max_retries)

        try:
            reponse = await client.post(
                url,
                params={"key": cle},
                json=corps,
                headers={"Content-Type": "application/json"},
            )
        except httpx.TimeoutException as exc:
            derniere_erreur = HTTPException(
                status_code=504,
                detail="Délai d'attente dépassé (timeout 30s) lors de l'appel au modèle multimodal Gemini.",
            )
            if est_dernier_essai:
                break
            journal.warning(
                "Gemini (%s) timeout à la tentative %d/%d. Nouvelle tentative dans %.1fs...",
                modele, tentative + 1, max_retries, delai,
            )
            await asyncio.sleep(delai)
            continue
        except httpx.RequestError as exc:
            derniere_erreur = HTTPException(
                status_code=502,
                detail=f"Erreur de communication réseau avec l'API Gemini : {exc}",
            )
            if est_dernier_essai:
                break
            journal.warning(
                "Gemini (%s) erreur réseau à la tentative %d/%d : %r. Nouvelle tentative dans %.1fs...",
                modele, tentative + 1, max_retries, exc, delai,
            )
            await asyncio.sleep(delai)
            continue

        # ── Cas de succès HTTP 200 ──
        if reponse.status_code == 200:
            try:
                return reponse.json(), None
            except Exception as exc:
                derniere_erreur = HTTPException(
                    status_code=502,
                    detail=f"Réponse JSON invalide reçue du modèle Gemini : {exc}",
                )
                if est_dernier_essai:
                    break
                await asyncio.sleep(delai)
                continue

        # ── Erreurs client non rejouables (400, 401, 403) : arrêt immédiat ──
        if reponse.status_code in (400, 401, 403):
            detail_msg = f"Clé API Gemini invalide ou requête rejetée (HTTP {reponse.status_code})."
            try:
                err_data = reponse.json()
                if "error" in err_data and "message" in err_data["error"]:
                    detail_msg = f"Erreur API Gemini ({reponse.status_code}) : {err_data['error']['message']}"
            except Exception:
                pass
            return None, HTTPException(status_code=reponse.status_code, detail=detail_msg)

        # ── Modèle introuvable (404) : inutile de retenter, arrêt immédiat pour repli éventuel ──
        if reponse.status_code == 404:
            detail_msg = f"Modèle Gemini '{modele}' introuvable (HTTP 404)."
            try:
                err_data = reponse.json()
                if "error" in err_data and "message" in err_data["error"]:
                    detail_msg = f"Erreur API Gemini (404) : {err_data['error']['message']}"
            except Exception:
                pass
            return None, HTTPException(status_code=404, detail=detail_msg)

        # ── Gestion spécifique HTTP 503 : Service indisponible (JAMAIS une erreur de clé API) ──
        if reponse.status_code == 503:
            derniere_erreur = HTTPException(
                status_code=503,
                detail=(
                    "Service Gemini temporairement indisponible (HTTP 503). "
                    "Le service est actuellement surchargé ou en maintenance. "
                    "Ce problème est temporaire et ne provient pas de votre clé API. "
                    "Veuillez réessayer ultérieurement."
                ),
            )
            if est_dernier_essai:
                break
            journal.warning(
                "Gemini (%s) indisponible (HTTP 503) à la tentative %d/%d. Nouvelle tentative dans %.1fs...",
                modele, tentative + 1, max_retries, delai,
            )
            await asyncio.sleep(delai)
            continue

        # ── Gestion spécifique HTTP 429 : Quota / Rate limit ──
        if reponse.status_code == 429:
            derniere_erreur = HTTPException(
                status_code=429,
                detail="Quota de l'API Gemini dépassé (HTTP 429 Rate limit). Veuillez patienter ou vérifier votre quota.",
            )
            if est_dernier_essai:
                break
            journal.warning(
                "Gemini (%s) quota dépassé (HTTP 429) à la tentative %d/%d. Nouvelle tentative dans %.1fs...",
                modele, tentative + 1, max_retries, delai,
            )
            await asyncio.sleep(delai)
            continue

        # ── Gestion spécifique HTTP 502 / 500 : Erreur passerelle ou serveur distant ──
        if reponse.status_code in (500, 502):
            derniere_erreur = HTTPException(
                status_code=502,
                detail=f"Erreur de communication ou serveur du modèle Gemini (HTTP {reponse.status_code}) : {reponse.text[:200]}",
            )
            if est_dernier_essai:
                break
            journal.warning(
                "Gemini (%s) erreur serveur HTTP %d à la tentative %d/%d. Nouvelle tentative dans %.1fs...",
                modele, reponse.status_code, tentative + 1, max_retries, delai,
            )
            await asyncio.sleep(delai)
            continue

        # Tout autre code inattendu
        derniere_erreur = HTTPException(
            status_code=502,
            detail=f"Erreur inattendue retournée par le modèle Gemini (HTTP {reponse.status_code}) : {reponse.text[:200]}",
        )
        if est_dernier_essai:
            break
        await asyncio.sleep(delai)

    return None, derniere_erreur


async def _analyser_gemini(
    donnees: bytes,
    media_type: MediaType,
    format_detecte: str,
    delais: Optional[list[float]] = None,
    max_retries: Optional[int] = None,
) -> MediaAnalysisResult:
    """
    Envoie les véritables octets du fichier à l'API Gemini Vision multimodale.
    Gère rigoureusement le retry automatique, le basculement sur modèle alternatif
    compatible si configuré, et ne replie JAMAIS silencieusement sur un mock.
    """
    cle = (GEMINI_API_KEY or "").strip()
    if not cle:
        raise HTTPException(
            status_code=401,
            detail=(
                "Clé API Gemini absente. Veuillez définir GEMINI_API_KEY dans votre fichier .env "
                "pour activer l'analyse multimodale réelle."
            ),
        )

    mime = _mime_pour_gemini(media_type, format_detecte)
    b64 = base64.b64encode(donnees).decode("ascii")
    prompt = _prompt_pour(media_type)

    corps = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ]
            }
        ]
    }

    modele_principal = GEMINI_MODEL
    modele_repli = (GEMINI_FALLBACK_MODEL or "").strip()
    modele_utilise = modele_principal
    repli_utilise = False

    async with httpx.AsyncClient(timeout=30.0) as client:
        donnees_json, erreur = await _appeler_gemini_endpoint(
            client=client,
            modele=modele_principal,
            cle=cle,
            corps=corps,
            delais=delais,
            max_retries=max_retries,
        )

        # Si le modèle principal a échoué (indisponibilité 503, 502, 504, 404, 429)
        # et qu'un modèle alternatif distinct est configuré :
        if donnees_json is None and erreur is not None:
            peut_basculer = (
                bool(modele_repli)
                and modele_repli != modele_principal
                and erreur.status_code in (503, 502, 504, 404, 429)
            )
            if peut_basculer:
                journal.warning(
                    "Modèle principal '%s' indisponible (HTTP %d). Bascule sur le modèle alternatif compatible '%s'...",
                    modele_principal, erreur.status_code, modele_repli,
                )
                donnees_json_repli, erreur_repli = await _appeler_gemini_endpoint(
                    client=client,
                    modele=modele_repli,
                    cle=cle,
                    corps=corps,
                    delais=delais,
                    max_retries=max_retries,
                )
                if donnees_json_repli is not None:
                    donnees_json = donnees_json_repli
                    modele_utilise = modele_repli
                    repli_utilise = True
                    erreur = None
                else:
                    journal.error(
                        "Le modèle alternatif '%s' a également échoué : %s",
                        modele_repli, getattr(erreur_repli, 'detail', str(erreur_repli)),
                    )
                    raise erreur_repli or erreur
            else:
                raise erreur

    try:
        texte = donnees_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        candidates = donnees_json.get("candidates", []) if isinstance(donnees_json, dict) else []
        if candidates and "finishReason" in candidates[0]:
            reason = candidates[0].get("finishReason")
            raise HTTPException(
                status_code=422,
                detail=f"L'analyse de l'image n'a pas pu aboutir (Raison du modèle : {reason}).",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"Réponse inattendue reçue du modèle Gemini : {donnees_json}",
        ) from exc

    return MediaAnalysisResult(
        media_type=media_type,
        format_detecte=format_detecte,
        taille_octets=len(donnees),
        texte_extrait=texte,
        confiance=0.95,
        mode="real",
        metadata={
            "gemini_model": modele_utilise,
            "provider": "gemini",
            "fallback_used": repli_utilise,
            "primary_model": modele_principal,
        },
    )


# ── Point d'entrée public ─────────────────────────────────────────────────────

async def analyser_media(
    donnees: bytes,
    media_type: MediaType,
    format_detecte: str,
    forcer_simule: bool = False,
    delais: Optional[list[float]] = None,
    max_retries: Optional[int] = None,
) -> MediaAnalysisResult:
    """
    Analyse un fichier multimédia validé.

    Paramètres :
      donnees        : contenu binaire réel du fichier
      media_type     : MediaType.image ou MediaType.audio
      format_detecte : valeur d'ImageFormat ou AudioFormat (ex. "jpeg", "png")
      forcer_simule  : force le mode simulé (pour tests déterministes)
      delais         : liste personnalisée de délais de backoff (optionnel, pour tests rapides)
      max_retries    : nombre maximal de retries (optionnel, défaut 4)

    Règle d'or :
      En mode "real", on analyse réellement le fichier avec Gemini Vision.
      En cas d'erreur (clé absente, quota, modèle), une HTTPException est levée.
      AUCUN repli silencieux vers une réponse simulée n'est autorisé en mode réel.
    """
    mode_actuel = MODE.lower() if MODE else "mock"
    utiliser_reel = (mode_actuel == "real") and not forcer_simule

    if utiliser_reel:
        return await _analyser_gemini(
            donnees=donnees,
            media_type=media_type,
            format_detecte=format_detecte,
            delais=delais,
            max_retries=max_retries,
        )

    return _analyser_simule(donnees, media_type, format_detecte)
