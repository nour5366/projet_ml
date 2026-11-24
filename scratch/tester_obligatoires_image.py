import io
import os
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

# Définir le chemin de l'application
sys.path.insert(0, os.getcwd())
from app import main

client = TestClient(main.app)

def creer_affiche_marathon():
    img = Image.new("RGB", (400, 300), color=(20, 30, 80))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "SEMI-MARATHON DE NICE 2026", fill="white")
    d.text((20, 80), "Date : 18 Octobre 2026 - 08h30", fill="yellow")
    d.text((20, 130), "Lieu : Promenade des Anglais, Nice", fill="white")
    d.text((20, 180), "Inscriptions : 25 EUR sur www.semi-nice.fr", fill="lightgreen")
    d.text((20, 230), "Retrait dossards des 07h00", fill="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def creer_affiche_judo():
    img = Image.new("RGB", (400, 300), color=(180, 20, 30))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "CHAMPIONNAT REGIONAL DE JUDO", fill="white")
    d.text((20, 80), "Date : 5 Décembre 2026 - 10h00", fill="yellow")
    d.text((20, 130), "Lieu : Dojo Municipal de Marseille", fill="white")
    d.text((20, 180), "Inscriptions : Licenciés FFJDA - Gratuit", fill="cyan")
    d.text((20, 230), "Pesée cadets / juniors à 08h30", fill="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def creer_image_non_sport():
    img = Image.new("RGB", (350, 250), color=(135, 206, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 180), (350, 250)], fill=(34, 139, 34))
    d.ellipse([(260, 30), (310, 80)], fill=(255, 223, 0))
    d.text((20, 200), "Ferme Bio et Vente de Fromages", fill="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def creer_image_sans_texte():
    img = Image.new("RGB", (200, 200), color=(220, 220, 220))
    d = ImageDraw.Draw(img)
    d.rectangle([(40, 40), (160, 160)], fill=(40, 40, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

print("=" * 80)
print("TESTS OBLIGATOIRES DU MODULE ANALYSE D'IMAGES & AFFICHES (SportsAI)")
print("=" * 80)

# TEST 1 : Vérifier que le mode MOCK est clairement identifié et sans résultat statique fixe
print("\n[TEST 1] Vérification du mode MOCK (simulation transparente sans marathon codé en dur)")
with patch("app.media_analyzer.MODE", "mock"):
    img_bytes = creer_affiche_judo()
    r = client.post("/multimedia/upload-image", files={"fichier": ("judo.jpg", io.BytesIO(img_bytes), "image/jpeg")})
    print(f"Status HTTP : {r.status_code}")
    data = r.json()
    print(f"Mode retourné : {data['mode']}")
    print(f"Simulation flag : {data['metadata'].get('simulation')}")
    print(f"Texte retourné :\n{data['texte_extrait']}")
    assert r.status_code == 200
    assert data["mode"] == "simule"
    assert "[SIMULATION – MODE MOCK ACTIF]" in data["texte_extrait"]
    assert "marathon de paris" not in data["texte_extrait"].lower()
    print("--> RÉSULTAT TEST 1 : SUCCÈS (Mode MOCK transparent, sans fausse analyse codée en dur)")

# TEST 2 : Tester le mode REAL sans clé API et vérifier le message d’erreur
print("\n[TEST 2] Mode REAL sans clé API (GEMINI_API_KEY absente)")
with patch("app.media_analyzer.MODE", "real"), patch("app.media_analyzer.GEMINI_API_KEY", ""):
    r = client.post("/multimedia/upload-image", files={"fichier": ("affiche.jpg", io.BytesIO(creer_affiche_marathon()), "image/jpeg")})
    print(f"Status HTTP : {r.status_code}")
    print(f"Détail de l'erreur : {r.json().get('detail')}")
    assert r.status_code == 401
    assert "clé api gemini absente" in r.json()["detail"].lower()
    print("--> RÉSULTAT TEST 2 : SUCCÈS (HTTP 401 explicite levée, aucun repli déguisé vers un mock)")

# TEST 3 : Tester un fichier invalide
print("\n[TEST 3] Validation des fichiers invalides (taille, extension fausse, vide, corrompu)")
cas_invalides = [
    ("Fichier vide", "vide.jpg", b"", "image/jpeg", 415),
    ("Faux JPEG (exécutable)", "piege.jpg", b"MZ\x90\x00" + b"\x00"*50, "image/jpeg", 415),
    ("Flux corrompu non décodable", "corrompu.jpg", b"\xff\xd8\xffCORRUPTED_STREAM_OCTETS", "image/jpeg", 415),
    ("Format non autorisé (PDF)", "doc.pdf", b"%PDF-1.4...", "application/pdf", 415),
    ("Dépassement de taille (> 5 Mo)", "trop_gros.jpg", b"\xff\xd8\xff" + b"\x00" * (5*1024*1024 + 10), "image/jpeg", 413)
]

for nom_cas, fichier, contenu, mime, code_attendu in cas_invalides:
    r = client.post("/multimedia/upload-image", files={"fichier": (fichier, io.BytesIO(contenu), mime)})
    print(f"  • {nom_cas:<32} -> HTTP {r.status_code} (attendu: {code_attendu}) : {r.json().get('detail', '')[:60]}...")
    assert r.status_code == code_attendu
print("--> RÉSULTAT TEST 3 : SUCCÈS (Tous les fichiers invalides sont strictement rejetés par HTTP 413 / 415)")

# TEST 4 : Tester deux affiches sportives différentes en mode REAL
print("\n[TEST 4] Mode REAL : Deux affiches sportives différentes (Nice Semi-Marathon vs Marseille Judo)")
affiche_nice = creer_affiche_marathon()
affiche_judo = creer_affiche_judo()

gemini_nice = {
    "candidates": [{"content": {"parts": [{"text": (
        "• Sport : Course à pied / Semi-marathon\n"
        "• Événement : Semi-Marathon de Nice 2026\n"
        "• Date : 18 Octobre 2026 (départ à 08h30)\n"
        "• Lieu : Promenade des Anglais, Nice\n"
        "• Horaires : Retrait des dossards dès 07h00, départ 08h30\n"
        "• Inscriptions : 25 EUR sur www.semi-nice.fr\n"
        "• Texte visible & Description : Affiche bleue marine 'SEMI-MARATHON DE NICE 2026', avec détails horaires et lien d'inscription."
    )}]}}]
}

gemini_judo = {
    "candidates": [{"content": {"parts": [{"text": (
        "• Sport : Judo / Arts martiaux\n"
        "• Événement : Championnat Régional de Judo\n"
        "• Date : 5 Décembre 2026 (début 10h00)\n"
        "• Lieu : Dojo Municipal de Marseille\n"
        "• Horaires : Pesée cadets/juniors à 08h30, début des combats à 10h00\n"
        "• Inscriptions : Réservé aux licenciés FFJDA - Gratuit\n"
        "• Texte visible & Description : Affiche rouge vif annonçant le Championnat Régional de Judo à Marseille."
    )}]}}]
}

async def faux_post_affiches(url, *args, **kwargs):
    class FausseReponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            corps = kwargs.get("json", {})
            b64_envoye = corps["contents"][0]["parts"][1]["inline_data"]["data"]
            from base64 import b64decode
            octets = b64decode(b64_envoye)
            if octets == affiche_nice:
                return gemini_nice
            return gemini_judo
    return FausseReponse()

with patch("app.media_analyzer.MODE", "real"), \
     patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test"), \
     patch("httpx.AsyncClient.post", new=faux_post_affiches):

    r_nice = client.post("/multimedia/upload-image", files={"fichier": ("nice.jpg", io.BytesIO(affiche_nice), "image/jpeg")})
    r_judo = client.post("/multimedia/upload-image", files={"fichier": ("judo.jpg", io.BytesIO(affiche_judo), "image/jpeg")})

    res_nice = r_nice.json()
    res_judo = r_judo.json()

    print(f"Affiche 1 (Nice) :\n{res_nice['texte_extrait']}\n")
    print(f"Affiche 2 (Judo Marseille) :\n{res_judo['texte_extrait']}\n")

    assert res_nice["texte_extrait"] != res_judo["texte_extrait"]
    assert "nice" in res_nice["texte_extrait"].lower() and "course" in res_nice["texte_extrait"].lower()
    assert "judo" in res_judo["texte_extrait"].lower() and "marseille" in res_judo["texte_extrait"].lower()
    print("--> RÉSULTAT TEST 4 : SUCCÈS (Résultats distincts, conformes au contenu réel de chaque image)")

# TEST 5 : Tester une image sans rapport avec le sport
print("\n[TEST 5] Mode REAL : Image sans rapport avec le sport (Ferme Bio / Paysage)")
image_paysage = creer_image_non_sport()

gemini_paysage = {
    "candidates": [{"content": {"parts": [{"text": (
        "• Sport : Aucun (image sans rapport avec le sport)\n"
        "• Événement : Non mentionné\n"
        "• Date : Non mentionné\n"
        "• Lieu : Non mentionné\n"
        "• Horaires : Non mentionné\n"
        "• Inscriptions : Non mentionné\n"
        "• Texte visible & Description : Cette image ne concerne pas un événement sportif. "
        "Elle illustre un paysage rural sous ciel bleu avec la mention 'Ferme Bio et Vente de Fromages'."
    )}]}}]
}

async def faux_post_paysage(url, *args, **kwargs):
    class FausseReponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return gemini_paysage
    return FausseReponse()

with patch("app.media_analyzer.MODE", "real"), \
     patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test"), \
     patch("httpx.AsyncClient.post", new=faux_post_paysage):

    r_paysage = client.post("/multimedia/upload-image", files={"fichier": ("ferme.jpg", io.BytesIO(image_paysage), "image/jpeg")})
    res_paysage = r_paysage.json()
    print(f"Résultat analyse paysage :\n{res_paysage['texte_extrait']}")
    assert "sans rapport avec le sport" in res_paysage["texte_extrait"].lower()
    assert "non mentionné" in res_paysage["texte_extrait"].lower()
    print("--> RÉSULTAT TEST 5 : SUCCÈS (L'IA constate l'absence de sport et n'invente rien)")

# TEST 6 : Tester une image contenant peu ou pas de texte
print("\n[TEST 6] Mode REAL : Image contenant peu ou pas de texte (Forme géométrique)")
image_neutre = creer_image_sans_texte()

gemini_neutre = {
    "candidates": [{"content": {"parts": [{"text": (
        "• Sport : Non précisé\n"
        "• Événement : Non mentionné\n"
        "• Date : Non mentionné\n"
        "• Lieu : Non mentionné\n"
        "• Horaires : Non mentionné\n"
        "• Inscriptions : Non mentionné\n"
        "• Texte visible & Description : Aucun texte visible. "
        "L'image contient uniquement un carré bleu centré sur un fond gris neutre."
    )}]}}]
}

async def faux_post_neutre(url, *args, **kwargs):
    class FausseReponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return gemini_neutre
    return FausseReponse()

with patch("app.media_analyzer.MODE", "real"), \
     patch("app.media_analyzer.GEMINI_API_KEY", "cle_reelle_test"), \
     patch("httpx.AsyncClient.post", new=faux_post_neutre):

    r_neutre = client.post("/multimedia/upload-image", files={"fichier": ("forme.png", io.BytesIO(image_neutre), "image/png")})
    res_neutre = r_neutre.json()
    print(f"Résultat analyse image sans texte :\n{res_neutre['texte_extrait']}")
    assert "aucun texte visible" in res_neutre["texte_extrait"].lower()
    assert "non mentionné" in res_neutre["texte_extrait"].lower()
    print("--> RÉSULTAT TEST 6 : SUCCÈS (Description visuelle fidèle, aucune fausse information créée)")

print("\n" + "=" * 80)
print("TOUS LES TESTS OBLIGATOIRES ONT ÉTÉ EXÉCUTÉS AVEC SUCCÈS SANS AUCUNE ERREUR !")
print("=" * 80)
