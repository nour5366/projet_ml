"""Tests exhaustifs de la gestion des erreurs HTTP 503, 502, 429, retry avec exponential backoff et modèle alternatif."""
import asyncio
import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.media_analyzer import analyser_media
from app.schemas import MediaType

client = TestClient(main.app)


def _creer_image_jpeg() -> bytes:
    img = Image.new("RGB", (100, 100), color=(10, 80, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class MockHttpxResponse:
    """Simulateur de réponse HTTP pour httpx.AsyncClient.post."""
    def __init__(self, status_code: int = 200, json_data: dict = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or str(json_data)

    def json(self):
        return self._json_data


# ── 1. Succès immédiat (aucun réessai) ──────────────────────────────────────────

@pytest.mark.anyio
async def test_succes_immediat_sans_retry():
    """Un appel qui répond 200 du premier coup ne déclenche aucun retry ni aucun sleep."""
    reponse_ok = {
        "candidates": [{
            "content": {"parts": [{"text": "• Sport : Tennis\n• Événement : Tournoi de Nice"}]}
        }]
    }

    mock_post = AsyncMock(return_value=MockHttpxResponse(200, reponse_ok))
    mock_sleep = AsyncMock()

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_MODEL", "gemini-2.0-flash"), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", new=mock_sleep):

        res = await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert res.mode == "real"
        assert "tennis" in res.texte_extrait.lower()
        assert res.metadata["gemini_model"] == "gemini-2.0-flash"
        assert res.metadata["fallback_used"] is False
        assert mock_post.call_count == 1
        assert mock_sleep.call_count == 0


# ── 2. Récupération après erreur 503 transitoire (Retry & Backoff) ─────────────

@pytest.mark.anyio
async def test_recuperation_apres_503_transitoire():
    """Panne 503 sur le 1er appel, puis 200 au 2e appel : backoff de 1s respecté."""
    reponse_ok = {
        "candidates": [{
            "content": {"parts": [{"text": "• Sport : Natation\n• Événement : Meeting"}]}
        }]
    }

    mock_post = AsyncMock(side_effect=[
        MockHttpxResponse(503, text="Service Unavailable"),
        MockHttpxResponse(200, reponse_ok),
    ])
    delais_observes = []

    async def faux_sleep(d):
        delais_observes.append(d)

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_BACKOFF_DELAYS", [1.0, 2.0, 4.0, 8.0]), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", side_effect=faux_sleep):

        res = await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert mock_post.call_count == 2
        assert delais_observes == [1.0]
        assert "natation" in res.texte_extrait.lower()


@pytest.mark.anyio
async def test_recuperation_apres_plusieurs_503():
    """Panne 503 sur 3 appels, puis 200 au 4e appel : délais 1s, 2s, 4s respectés."""
    reponse_ok = {
        "candidates": [{
            "content": {"parts": [{"text": "• Sport : Judo"}]}
        }]
    }

    mock_post = AsyncMock(side_effect=[
        MockHttpxResponse(503, text="Service Unavailable"),
        MockHttpxResponse(503, text="Service Unavailable"),
        MockHttpxResponse(503, text="Service Unavailable"),
        MockHttpxResponse(200, reponse_ok),
    ])
    delais_observes = []

    async def faux_sleep(d):
        delais_observes.append(d)

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_BACKOFF_DELAYS", [1.0, 2.0, 4.0, 8.0]), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", side_effect=faux_sleep):

        res = await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert mock_post.call_count == 4
        assert delais_observes == [1.0, 2.0, 4.0]
        assert "judo" in res.texte_extrait.lower()


# ── 3. Indisponibilité persistante 503 (4 retries max, délais 1s, 2s, 4s, 8s) ─

@pytest.mark.anyio
async def test_indisponibilite_persistante_503_limitee_a_4_retries():
    """
    Si le 503 persiste :
      - Exactement 4 tentatives de réessai (5 appels au total : 1 initial + 4 retries).
      - Délais d'attente strictement égaux à [1.0, 2.0, 4.0, 8.0].
      - Exception HTTP 503 levée.
      - Ne mentionne JAMAIS une erreur de clé API.
    """
    mock_post = AsyncMock(return_value=MockHttpxResponse(503, text="Gemini backend unavailable"))
    delais_observes = []

    async def faux_sleep(d):
        delais_observes.append(d)

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", ""), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 4), \
         patch("app.media_analyzer.GEMINI_BACKOFF_DELAYS", [1.0, 2.0, 4.0, 8.0]), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", side_effect=faux_sleep):

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail.lower()

        # Règle 5 : Ne jamais considérer un 503 comme une erreur de clé API
        assert "ne provient pas de votre clé api" in detail
        assert "clé api invalide" not in detail
        assert "indisponible" in detail

        # Objectifs 2 & 3 : 4 retries maximum avec exponential backoff [1, 2, 4, 8]
        assert delais_observes == [1.0, 2.0, 4.0, 8.0]
        assert mock_post.call_count == 5  # 1 appel initial + 4 réessais


# ── 4. Gestion spécifique des erreurs 502 et 429 ──────────────────────────────

@pytest.mark.anyio
async def test_gestion_specifique_erreur_502():
    """HTTP 502 répété déclenche les retries et remonte un code HTTP 502 explicite."""
    mock_post = AsyncMock(return_value=MockHttpxResponse(502, text="Bad Gateway upstream"))
    delais_observes = []

    async def faux_sleep(d):
        delais_observes.append(d)

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", ""), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 4), \
         patch("app.media_analyzer.GEMINI_BACKOFF_DELAYS", [1.0, 2.0, 4.0, 8.0]), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", side_effect=faux_sleep):

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert exc_info.value.status_code == 502
        assert "passerelle" in exc_info.value.detail.lower() or "communication" in exc_info.value.detail.lower()
        assert len(delais_observes) == 4


@pytest.mark.anyio
async def test_gestion_specifique_erreur_429():
    """HTTP 429 (Rate limit) répété déclenche les retries et remonte un code HTTP 429."""
    mock_post = AsyncMock(return_value=MockHttpxResponse(429, text="Resource exhausted"))
    delais_observes = []

    async def faux_sleep(d):
        delais_observes.append(d)

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", ""), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 4), \
         patch("app.media_analyzer.GEMINI_BACKOFF_DELAYS", [1.0, 2.0, 4.0, 8.0]), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", side_effect=faux_sleep):

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert exc_info.value.status_code == 429
        assert "quota" in exc_info.value.detail.lower()
        assert len(delais_observes) == 4


# ── 5. Erreurs non-retryables (400, 401, 403) : aucun réessai ────────────────

@pytest.mark.anyio
async def test_erreur_cle_400_ne_declenche_aucun_retry():
    """Une clé API invalide (HTTP 400/401) échoue immédiatement sans réessais inutiles."""
    reponse_400 = {
        "error": {
            "code": 400,
            "message": "API key not valid. Please pass a valid API key.",
            "status": "INVALID_ARGUMENT",
        }
    }
    mock_post = AsyncMock(return_value=MockHttpxResponse(400, reponse_400))
    mock_sleep = AsyncMock()

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_invalide"), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", new=mock_sleep):

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert exc_info.value.status_code == 400
        assert "api key not valid" in exc_info.value.detail.lower()
        assert mock_post.call_count == 1
        assert mock_sleep.call_count == 0


# ── 6. Modèle alternatif compatible (Fallback) ────────────────────────────────

@pytest.mark.anyio
async def test_fallback_sur_modele_alternatif_apres_echec_principal():
    """
    Si le modèle principal reste indisponible (503 sur toutes les tentatives) :
      - Bascule automatique sur GEMINI_FALLBACK_MODEL configuré.
      - Si le modèle de secours répond 200, le résultat est retourné avec succès.
      - Les métadonnées indiquent fallback_used: True et le modèle utilisé.
    """
    reponse_ok_fallback = {
        "candidates": [{
            "content": {"parts": [{"text": "• Sport : Escalade (analysé par fallback)"}]}
        }]
    }

    appels_modeles = []

    async def faux_post(*args, **kwargs):
        # url peut être en position 0 ou 1 selon le binding de la méthode
        url = args[1] if len(args) > 1 and isinstance(args[1], str) else args[0]
        if "gemini-3.8-flash" in str(url):
            appels_modeles.append("gemini-3.8-flash")
            return MockHttpxResponse(503, text="Service Unavailable")
        elif "gemini-2.0-flash" in str(url):
            appels_modeles.append("gemini-2.0-flash")
            return MockHttpxResponse(200, reponse_ok_fallback)
        return MockHttpxResponse(500)

    mock_sleep = AsyncMock()

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_MODEL", "gemini-3.8-flash"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", "gemini-2.0-flash"), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 4), \
         patch("httpx.AsyncClient.post", new=faux_post), \
         patch("asyncio.sleep", new=mock_sleep):

        res = await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert res.mode == "real"
        assert "escalade" in res.texte_extrait.lower()
        assert res.metadata["gemini_model"] == "gemini-2.0-flash"
        assert res.metadata["fallback_used"] is True
        assert res.metadata["primary_model"] == "gemini-3.8-flash"

        # Le modèle principal a été essayé avec ses retries, puis le modèle de repli a réussi
        assert "gemini-3.8-flash" in appels_modeles
        assert "gemini-2.0-flash" in appels_modeles


@pytest.mark.anyio
async def test_fallback_echec_des_deux_modeles():
    """Si le modèle principal ET le modèle de repli échouent tous les deux, 503 est levé."""
    mock_post = AsyncMock(return_value=MockHttpxResponse(503, text="Service Unavailable everywhere"))
    mock_sleep = AsyncMock()

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_MODEL", "gemini-3.8-flash"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", "gemini-2.0-flash"), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 2), \
         patch("httpx.AsyncClient.post", new=mock_post), \
         patch("asyncio.sleep", new=mock_sleep):

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await analyser_media(_creer_image_jpeg(), MediaType.image, "jpeg")

        assert exc_info.value.status_code == 503


# ── 7. Test d'intégration via la route HTTP /multimedia/upload-image ───────────

def test_route_upload_image_renvoie_503_explicite_sans_confondre_avec_cle():
    """Vérification via le TestClient FastAPI que l'endpoint /multimedia/upload-image propage bien 503."""
    async def faux_post(url, *args, **kwargs):
        return MockHttpxResponse(503, text="Service Unavailable")

    mock_sleep = AsyncMock()

    with patch("app.media_analyzer.MODE", "real"), \
         patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide_test"), \
         patch("app.media_analyzer.GEMINI_FALLBACK_MODEL", ""), \
         patch("app.media_analyzer.GEMINI_MAX_RETRIES", 4), \
         patch("httpx.AsyncClient.post", new=faux_post), \
         patch("asyncio.sleep", new=mock_sleep):

        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("affiche.jpg", io.BytesIO(_creer_image_jpeg()), "image/jpeg")},
        )

        assert r.status_code == 503
        data = r.json()
        assert "503" in data["detail"]
        assert "ne provient pas de votre clé api" in data["detail"].lower()
