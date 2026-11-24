"""Tests du bonus multimédia : images et audios.

Couverture :
  ✅ Image JPEG valide → 200 + texte simulé
  ✅ Image PNG valide  → 200 + texte simulé
  ✅ Image WEBP valide → 200 + texte simulé
  ❌ Image trop grande → 413
  ❌ MIME image non supporté (PDF déclaré) → 415
  ❌ Image corrompu (mauvaise signature) → 415
  ❌ Fichier vide    → 415
  ✅ Audio WAV valide → 200 + texte simulé
  ✅ Audio MP3 valide → 200 + texte simulé
  ✅ Audio OGG valide → 200 + texte simulé
  ❌ Audio trop grand → 413
  ❌ MIME audio non supporté → 415
  ❌ Audio corrompu  → 415
  ✅ Les anciens tests (texte) ne régressent pas
"""
import io
import struct
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import MAX_AUDIO_SIZE_BYTES, MAX_IMAGE_SIZE_BYTES

client = TestClient(main.app)

# ─────────────────────────────────────────────────────────────────────────────
# Générateurs de fichiers synthétiques minimalistes
# (formats valides, petits, sans dépendance externe)
# ─────────────────────────────────────────────────────────────────────────────

def _creer_jpeg_minimal() -> bytes:
    """Génère un JPEG valide 10x10 avec Pillow."""
    try:
        from PIL import Image
        buf = io.BytesIO()
        img = Image.new("RGB", (10, 10), color=(0, 128, 255))
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        return bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
            0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
            0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
            0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
            0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
            0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
            0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00,
            0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
            0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35,
            0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0x28, 0xA0, 0xFF, 0xD9,
        ])


def _creer_png_minimal() -> bytes:
    """PNG 1×1 pixel rouge (signature + IHDR + IDAT + IEND)."""
    # On utilise Pillow s'il est disponible, sinon on renvoie un PNG pré-codé.
    try:
        from PIL import Image
        buf = io.BytesIO()
        img = Image.new("RGB", (1, 1), color=(255, 0, 0))
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # PNG 1x1 rouge encodé en dur (67 octets)
        return bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
            0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82,
        ])


def _creer_webp_minimal() -> bytes:
    """WEBP minimal (container RIFF + marqueur WEBP)."""
    try:
        from PIL import Image
        buf = io.BytesIO()
        img = Image.new("RGB", (1, 1), color=(0, 255, 0))
        img.save(buf, format="WEBP")
        return buf.getvalue()
    except ImportError:
        # WEBP lossless 1×1 pixel minimaliste (20 octets)
        payload = b"\x2f\x00\x00\x00\x57\x45\x42\x50\x56\x50\x38\x4c"
        taille = len(payload) + 4
        return b"RIFF" + struct.pack("<I", taille) + payload


def _creer_wav_minimal() -> bytes:
    """WAV PCM 1 canal, 1 sample, 16 bits, 44100 Hz."""
    nb_canaux = 1
    freq = 44100
    bits = 16
    nb_samples = 1
    data = b"\x00\x00"   # 1 sample silencieux
    bloc = nb_canaux * bits // 8
    debit = freq * bloc
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(data))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, nb_canaux, freq, debit, bloc, bits)
        + b"data"
        + struct.pack("<I", len(data))
        + data
    )


def _creer_mp3_minimal() -> bytes:
    """En-tête MP3 avec ID3 (suffisant pour le magic bytes) suivi de silence."""
    # Tag ID3v2 minimaliste (10 octets d'en-tête)
    id3_header = b"ID3" + b"\x03\x00\x00" + b"\x00\x00\x00\x00"
    # Trame MP3 silencieuse (frame sync + données vides)
    mp3_frame = b"\xff\xfb\x90\x00" + b"\x00" * 413
    return id3_header + mp3_frame


def _creer_ogg_minimal() -> bytes:
    """OggS page minimale."""
    return b"OggS" + b"\x00" * 23 + b"\x01" + b"\x00" * 10


# ─────────────────────────────────────────────────────────────────────────────
# Tests images
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadImage:

    def test_jpeg_valide_renvoie_200(self):
        """Une image JPEG valide doit être acceptée et analysée (simulateur)."""
        donnees = _creer_jpeg_minimal()
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("photo.jpg", io.BytesIO(donnees), "image/jpeg")},
        )
        assert r.status_code == 200, r.text
        corps = r.json()
        assert corps["media_type"] == "image"
        assert corps["format_detecte"] == "jpeg"
        assert "simulé" in corps["texte_extrait"].lower() or "simulation" in corps["mode"]
        assert corps["taille_octets"] == len(donnees)

    def test_png_valide_renvoie_200(self):
        """Une image PNG valide doit être acceptée."""
        donnees = _creer_png_minimal()
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("image.png", io.BytesIO(donnees), "image/png")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["format_detecte"] == "png"

    def test_webp_valide_renvoie_200(self):
        """Une image WEBP valide doit être acceptée."""
        donnees = _creer_webp_minimal()
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("banniere.webp", io.BytesIO(donnees), "image/webp")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["format_detecte"] == "webp"

    def test_image_trop_grande_renvoie_413(self):
        """Un fichier dépassant la limite doit renvoyer 413."""
        trop_grand = b"\xff\xd8\xff" + b"\x00" * (MAX_IMAGE_SIZE_BYTES + 1)
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("gros.jpg", io.BytesIO(trop_grand), "image/jpeg")},
        )
        assert r.status_code == 413
        assert "trop grande" in r.json()["detail"].lower()

    def test_mime_non_supporte_renvoie_415(self):
        """Un fichier déclaré application/pdf doit être rejeté (415)."""
        donnees = b"%PDF-1.4 faux contenu"
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("piege.pdf", io.BytesIO(donnees), "application/pdf")},
        )
        assert r.status_code == 415

    def test_signature_binaire_invalide_renvoie_415(self):
        """Un fichier avec un MIME image/jpeg mais une signature EXE doit être rejeté."""
        donnees = b"MZ\x90\x00" + b"\x00" * 100   # signature d'un .exe Windows
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("piege.jpg", io.BytesIO(donnees), "image/jpeg")},
        )
        assert r.status_code == 415
        assert "signature" in r.json()["detail"].lower() or "format" in r.json()["detail"].lower()

    def test_fichier_vide_renvoie_415(self):
        """Un fichier vide doit être rejeté."""
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("vide.jpg", io.BytesIO(b""), "image/jpeg")},
        )
        assert r.status_code == 415
        assert "vide" in r.json()["detail"].lower()

    def test_reponse_contient_mode(self):
        """La réponse doit indiquer le mode (simule ou real)."""
        donnees = _creer_jpeg_minimal()
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("photo.jpg", io.BytesIO(donnees), "image/jpeg")},
        )
        assert r.status_code == 200
        assert r.json()["mode"] in ("simule", "real", "simule_repli")


# ─────────────────────────────────────────────────────────────────────────────
# Tests audios
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadAudio:

    def test_wav_valide_renvoie_200(self):
        """Un fichier WAV valide doit être accepté et analysé."""
        donnees = _creer_wav_minimal()
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("enregistrement.wav", io.BytesIO(donnees), "audio/wav")},
        )
        assert r.status_code == 200, r.text
        corps = r.json()
        assert corps["media_type"] == "audio"
        assert corps["format_detecte"] == "wav"
        assert len(corps["texte_extrait"]) > 0

    def test_mp3_valide_renvoie_200(self):
        """Un fichier MP3 valide (ID3 + frame) doit être accepté."""
        donnees = _creer_mp3_minimal()
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("audio.mp3", io.BytesIO(donnees), "audio/mpeg")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["format_detecte"] == "mp3"

    def test_ogg_valide_renvoie_200(self):
        """Un fichier OGG valide doit être accepté."""
        donnees = _creer_ogg_minimal()
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("voix.ogg", io.BytesIO(donnees), "audio/ogg")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["format_detecte"] == "ogg"

    def test_audio_trop_grand_renvoie_413(self):
        """Un fichier audio dépassant la limite doit renvoyer 413."""
        trop_grand = b"RIFF" + struct.pack("<I", MAX_AUDIO_SIZE_BYTES) + b"WAVE" + b"\x00" * MAX_AUDIO_SIZE_BYTES
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("gros.wav", io.BytesIO(trop_grand), "audio/wav")},
        )
        assert r.status_code == 413
        assert "trop grand" in r.json()["detail"].lower()

    def test_mime_audio_non_supporte_renvoie_415(self):
        """Un fichier déclaré video/mp4 doit être rejeté."""
        donnees = b"\x00\x00\x00\x20ftyp" + b"\x00" * 20
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("video.mp4", io.BytesIO(donnees), "video/mp4")},
        )
        assert r.status_code == 415

    def test_signature_audio_invalide_renvoie_415(self):
        """Un fichier avec MIME audio/wav mais signature PNG doit être rejeté."""
        donnees = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("piege.wav", io.BytesIO(donnees), "audio/wav")},
        )
        assert r.status_code == 415

    def test_audio_vide_renvoie_415(self):
        """Un fichier audio vide doit être rejeté."""
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("vide.wav", io.BytesIO(b""), "audio/wav")},
        )
        assert r.status_code == 415

    def test_reponse_audio_contient_transcription(self):
        """La réponse doit contenir un texte (simulé ou réel)."""
        donnees = _creer_wav_minimal()
        r = client.post(
            "/multimedia/upload-audio",
            files={"fichier": ("enregistrement.wav", io.BytesIO(donnees), "audio/wav")},
        )
        assert r.status_code == 200
        assert len(r.json()["texte_extrait"]) > 10


# ─────────────────────────────────────────────────────────────────────────────
# Tests de non-régression : les routes textuelles existantes fonctionnent encore
# ─────────────────────────────────────────────────────────────────────────────

class TestNonRegression:

    def test_health_toujours_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_assistant_toujours_ok(self):
        r = client.post("/assistant", json={"message": "Quels tournois de basket sont proposés ?"})
        assert r.status_code == 200
        corps = r.json()
        assert "reponse" in corps
        assert corps["provider"] == "mock"

    def test_validation_message_trop_court(self):
        assert client.post("/assistant", json={"message": "ab"}).status_code == 422

    def test_validation_message_vide(self):
        assert client.post("/assistant", json={}).status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Tests robustes du module Analyse d'Images & Affiches
# ─────────────────────────────────────────────────────────────────────────────

def _creer_affiche_tennis() -> bytes:
    """Génère une image d'affiche de tournoi de tennis."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (300, 200), color=(34, 139, 34))  # Vert court de tennis
    d = ImageDraw.Draw(img)
    d.text((20, 20), "TOURNOI OPEN DE TENNIS PARIS", fill="white")
    d.text((20, 60), "Date: 15 mai 2026", fill="yellow")
    d.text((20, 100), "Lieu: Court Central Paris", fill="white")
    d.text((20, 140), "Inscriptions ouvertes sur www.tennis-paris.fr", fill="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _creer_affiche_basket() -> bytes:
    """Génère une image d'affiche de tournoi de basketball 3x3."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (300, 200), color=(255, 140, 0))  # Orange basket
    d = ImageDraw.Draw(img)
    d.text((20, 20), "TOURNOI BASKET 3x3 LYON ALL-STARS", fill="black")
    d.text((20, 60), "Date: 20 juillet 2026", fill="blue")
    d.text((20, 100), "Lieu: Gymnase des Lilas Lyon", fill="black")
    d.text((20, 140), "Inscriptions 15E par equipe au 06.12.34.56.78", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _creer_image_paysage_non_sport() -> bytes:
    """Génère une image de paysage sans aucun rapport avec le sport."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (250, 150), color=(70, 130, 180))  # Bleu ciel
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 100), (250, 150)], fill=(34, 139, 34))  # Collines vertes
    d.ellipse([(180, 20), (220, 60)], fill=(255, 215, 0))    # Soleil
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _creer_image_sans_texte() -> bytes:
    """Génère une image purement graphique sans aucun texte."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    d.ellipse([(50, 50), (150, 150)], fill=(0, 0, 0))  # Cercle noir uni
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestAnalyseImagesExigences:
    """Vérification stricte de toutes les exigences demandées pour le module Image."""

    def test_mock_est_clairement_identifie_et_sans_marathon_fige(self):
        """En mode MOCK, l'analyse ne doit JAMAIS prétendre être un marathon ni une vraie analyse."""
        with patch("app.media_analyzer.MODE", "mock"):
            donnees = _creer_affiche_tennis()
            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("tennis.jpg", io.BytesIO(donnees), "image/jpeg")},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["mode"] == "simule"
            assert data["metadata"].get("simulation") is True
            assert "simulation – mode mock actif" in data["texte_extrait"].lower()
            # Interdiction absolue de la fausse analyse marathon
            assert "marathon de paris" not in data["texte_extrait"].lower()
            assert "300 × 200" in data["texte_extrait"] or "300" in data["texte_extrait"]

    def test_mode_real_sans_cle_api_renvoie_erreur_explicite_401(self):
        """En mode REAL sans clé API, renvoie HTTP 401 avec message clair, JAMAIS de mock silencieux."""
        with patch("app.media_analyzer.MODE", "real"), patch("app.media_analyzer.GEMINI_API_KEY", ""):
            donnees = _creer_jpeg_minimal()
            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("affiche.jpg", io.BytesIO(donnees), "image/jpeg")},
            )
            assert r.status_code == 401
            assert "clé api gemini absente" in r.json()["detail"].lower()

    def test_mode_real_deux_affiches_sportives_differentes(self):
        """Deux affiches sportives différentes doivent produire des résultats distincts fidèles au contenu."""
        affiche_tennis = _creer_affiche_tennis()
        affiche_basket = _creer_affiche_basket()

        reponse_gemini_tennis = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    "• Sport : Tennis\n"
                                    "• Événement : Tournoi Open de Tennis Paris\n"
                                    "• Date : 15 mai 2026\n"
                                    "• Lieu : Court Central Paris\n"
                                    "• Horaires : Non mentionné\n"
                                    "• Inscriptions : Ouvertes sur www.tennis-paris.fr\n"
                                    "• Texte visible & Description : Affiche sur fond vert avec inscription "
                                    "'TOURNOI OPEN DE TENNIS PARIS', date du 15 mai 2026."
                                )
                            }
                        ]
                    }
                }
            ]
        }

        reponse_gemini_basket = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    "• Sport : Basketball\n"
                                    "• Événement : Tournoi Basket 3x3 Lyon All-Stars\n"
                                    "• Date : 20 juillet 2026\n"
                                    "• Lieu : Gymnase des Lilas Lyon\n"
                                    "• Horaires : Non mentionné\n"
                                    "• Inscriptions : 15€ par équipe au 06.12.34.56.78\n"
                                    "• Texte visible & Description : Affiche orange annonçant le tournoi "
                                    "basket 3x3 de Lyon le 20 juillet 2026."
                                )
                            }
                        ]
                    }
                }
            ]
        }

        async def faux_post(url, *args, **kwargs):
            class FausseReponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self):
                    # On vérifie quel contenu binaire a été envoyé dans le corps
                    corps = kwargs.get("json", {})
                    b64_envoye = corps["contents"][0]["parts"][1]["inline_data"]["data"]
                    from base64 import b64decode
                    octets = b64decode(b64_envoye)
                    if octets == affiche_tennis:
                        return reponse_gemini_tennis
                    return reponse_gemini_basket

            return FausseReponse()

        with patch("app.media_analyzer.MODE", "real"), \
             patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test_valide"), \
             patch("httpx.AsyncClient.post", new=faux_post):

            r1 = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("tennis.jpg", io.BytesIO(affiche_tennis), "image/jpeg")},
            )
            r2 = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("basket.jpg", io.BytesIO(affiche_basket), "image/jpeg")},
            )

            assert r1.status_code == 200
            assert r2.status_code == 200

            data1 = r1.json()
            data2 = r2.json()

            assert data1["mode"] == "real"
            assert data2["mode"] == "real"

            # Les résultats sont obligatoirement distincts et correspondent aux données
            assert data1["texte_extrait"] != data2["texte_extrait"]
            assert "tennis" in data1["texte_extrait"].lower()
            assert "basket" in data2["texte_extrait"].lower()
            assert "paris" in data1["texte_extrait"].lower()
            assert "lyon" in data2["texte_extrait"].lower()

    def test_mode_real_image_sans_rapport_avec_le_sport(self):
        """Une image sans rapport avec le sport ne doit inventer aucune info sportive."""
        paysage = _creer_image_paysage_non_sport()

        reponse_gemini_paysage = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    "• Sport : Aucun (image sans rapport avec le sport)\n"
                                    "• Événement : Non mentionné\n"
                                    "• Date : Non mentionné\n"
                                    "• Lieu : Non mentionné\n"
                                    "• Horaires : Non mentionné\n"
                                    "• Inscriptions : Non mentionné\n"
                                    "• Texte visible & Description : Cette image représente un paysage illustré "
                                    "avec des collines verdoyantes sous un ciel bleu avec un soleil. "
                                    "Cette image ne concerne pas un événement sportif."
                                )
                            }
                        ]
                    }
                }
            ]
        }

        async def faux_post(url, *args, **kwargs):
            class FausseReponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return reponse_gemini_paysage
            return FausseReponse()

        with patch("app.media_analyzer.MODE", "real"), \
             patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test_valide"), \
             patch("httpx.AsyncClient.post", new=faux_post):

            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("paysage.jpg", io.BytesIO(paysage), "image/jpeg")},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["mode"] == "real"
            assert "sans rapport avec le sport" in data["texte_extrait"].lower()
            assert "marathon" not in data["texte_extrait"].lower()

    def test_mode_real_image_peu_ou_pas_de_texte(self):
        """Une image contenant peu ou pas de texte décrit la scène sans fabriquer d'inscriptions."""
        sans_texte = _creer_image_sans_texte()

        reponse_gemini_sans_texte = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    "• Sport : Non précisé\n"
                                    "• Événement : Non mentionné\n"
                                    "• Date : Non mentionné\n"
                                    "• Lieu : Non mentionné\n"
                                    "• Horaires : Non mentionné\n"
                                    "• Inscriptions : Non mentionné\n"
                                    "• Texte visible & Description : Aucun texte visible. "
                                    "L'image contient uniquement une forme géométrique sombre circulaire "
                                    "sur fond gris clair."
                                )
                            }
                        ]
                    }
                }
            ]
        }

        async def faux_post(url, *args, **kwargs):
            class FausseReponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return reponse_gemini_sans_texte
            return FausseReponse()

        with patch("app.media_analyzer.MODE", "real"), \
             patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test_valide"), \
             patch("httpx.AsyncClient.post", new=faux_post):

            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("forme.png", io.BytesIO(sans_texte), "image/png")},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["mode"] == "real"
            assert "aucun texte visible" in data["texte_extrait"].lower()
            assert "non mentionné" in data["texte_extrait"].lower()

    def test_mode_real_gestion_erreur_quota_429(self):
        """En cas de quota dépassé sur Gemini (429), le code 429 et le message d'erreur sont propagés."""
        async def faux_post(url, *args, **kwargs):
            class FausseReponse:
                status_code = 429
                text = "RESOURCE_EXHAUSTED: Quota exceeded for quota metric 'Generate Content API requests'"
                def json(self): return {"error": {"message": "Quota exceeded", "code": 429}}
            return FausseReponse()

        with patch("app.media_analyzer.MODE", "real"), \
             patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide"), \
             patch("httpx.AsyncClient.post", new=faux_post):

            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("photo.jpg", io.BytesIO(_creer_jpeg_minimal()), "image/jpeg")},
            )
            assert r.status_code == 429
            assert "quota" in r.json()["detail"].lower()

    def test_mode_real_gestion_erreur_modele_502(self):
        """En cas de panne ou d'erreur interne du modèle distant, renvoie 502 sans repli mock."""
        async def faux_post(url, *args, **kwargs):
            class FausseReponse:
                status_code = 500
                text = "Internal Server Error in Gemini Model cluster"
                def json(self): return {"error": {"message": "Internal error", "code": 500}}
            return FausseReponse()

        with patch("app.media_analyzer.MODE", "real"), \
             patch("app.media_analyzer.GEMINI_API_KEY", "cle_valide"), \
             patch("httpx.AsyncClient.post", new=faux_post):

            r = client.post(
                "/multimedia/upload-image",
                files={"fichier": ("photo.jpg", io.BytesIO(_creer_jpeg_minimal()), "image/jpeg")},
            )
            assert r.status_code == 502
            assert "modèle" in r.json()["detail"].lower()

    def test_image_corrompue_pil_renvoie_415(self):
        """Image avec magic bytes corrects mais données corrompues rejetée avec HTTP 415."""
        donnees_corrompues = b"\xff\xd8\xffCORRUPTED_STREAM_OCTETS_INVALIDE_12345"
        r = client.post(
            "/multimedia/upload-image",
            files={"fichier": ("corrompue.jpg", io.BytesIO(donnees_corrompues), "image/jpeg")},
        )
        assert r.status_code == 415
        assert "décadé" in r.json()["detail"].lower() or "décodé" in r.json()["detail"].lower()

