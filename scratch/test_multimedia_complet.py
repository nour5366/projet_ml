import io
import struct
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image

# Import de l'application
import os
# Répertoire courant
sys.path.insert(0, os.getcwd())
from app import main
from app.config import MAX_IMAGE_SIZE_BYTES, MAX_AUDIO_SIZE_BYTES

client = TestClient(main.app)

def creer_jpeg_valide():
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(30, 144, 255))
    img.save(buf, format="JPEG")
    return buf.getvalue()

def creer_png_valide():
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(255, 69, 0))
    img.save(buf, format="PNG")
    return buf.getvalue()

def creer_webp_valide():
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(50, 205, 50))
    img.save(buf, format="WEBP")
    return buf.getvalue()

def creer_wav_valide():
    nb_canaux = 1
    freq = 44100
    bits = 16
    data = b"\x00\x00" * 100
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

def creer_mp3_valide():
    id3 = b"ID3" + b"\x03\x00\x00" + b"\x00\x00\x00\x00"
    frame = b"\xff\xfb\x90\x00" + b"\x00" * 413
    return id3 + frame

def creer_ogg_valide():
    return b"OggS" + b"\x00" * 23 + b"\x01" + b"\x00" * 10

def creer_m4a_valide():
    # En-tête ISO Base Media File Format (ftyp) typique pour M4A
    atom_ftyp = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00M4A mp42isom"
    return atom_ftyp + b"\x00" * 100

print("=== CAMPAGNE DE TESTS MULTIMÉDIA (IMAGES & AUDIOS) ===")
resultats_mm = []

# --- 10 TESTS IMAGES ---
tests_images = [
    ("IMG-01", "Image JPEG valide", "photo.jpg", creer_jpeg_valide(), "image/jpeg", 200),
    ("IMG-02", "Image PNG valide", "logo.png", creer_png_valide(), "image/png", 200),
    ("IMG-03", "Image WEBP valide", "banniere.webp", creer_webp_valide(), "image/webp", 200),
    ("IMG-04", "Affiche réelle événement sportif (JPEG)", "affiche_marathon.jpg", creer_jpeg_valide(), "image/jpeg", 200),
    ("IMG-05", "Image sans rapport avec le sport", "paysage.jpg", creer_jpeg_valide(), "image/jpeg", 200),
    ("IMG-06", "Image illisible / corrompue", "corrompu.jpg", b"\xff\xd8\xffCORRUPTED_BYTES_HERE_12345", "image/jpeg", 415),
    ("IMG-07", "Extension fausse (EXE déguisé en JPG)", "piege.jpg", b"MZ\x90\x00" + b"\x00"*60, "image/jpeg", 415),
    ("IMG-08", "Type non supporté (PDF)", "document.pdf", b"%PDF-1.4...", "application/pdf", 415),
    ("IMG-09", "Fichier dépassant limite taille (5 Mo)", "trop_gros.jpg", b"\xff\xd8\xff" + b"\x00" * (MAX_IMAGE_SIZE_BYTES + 10), "image/jpeg", 413),
    ("IMG-10", "Fichier vide (0 octet)", "vide.jpg", b"", "image/jpeg", 415),
]

for tid, desc, nom, contenu, mime, attendu in tests_images:
    t0 = time.perf_counter()
    r = client.post("/multimedia/upload-image", files={"fichier": (nom, io.BytesIO(contenu), mime)})
    lat = round((time.perf_counter() - t0) * 1000, 2)
    statut = "PASS" if r.status_code == attendu else "FAIL"
    resultats_mm.append((tid, desc, attendu, r.status_code, lat, statut))
    print(f"[{tid}] {desc:<45} | Attendu: {attendu} | Obtenu: {r.status_code} ({lat} ms) -> {statut}")

# --- 11 TESTS AUDIOS ---
tests_audios = [
    ("AUD-01", "Audio WAV valide", "audio.wav", creer_wav_valide(), "audio/wav", 200),
    ("AUD-02", "Audio MP3 valide", "son.mp3", creer_mp3_valide(), "audio/mpeg", 200),
    ("AUD-03", "Audio M4A valide", "voix.m4a", creer_m4a_valide(), "audio/mp4", 200),
    ("AUD-04", "Audio OGG valide", "message.ogg", creer_ogg_valide(), "audio/ogg", 200),
    ("AUD-05", "Audio demande inscription (WAV)", "inscription.wav", creer_wav_valide(), "audio/wav", 200),
    ("AUD-06", "Audio silencieux (WAV)", "silence.wav", creer_wav_valide(), "audio/wav", 200),
    ("AUD-07", "Audio incompréhensible / bruit", "bruit.wav", creer_wav_valide(), "audio/wav", 200),
    ("AUD-08", "Audio corrompu (RIFF tronqué)", "corrompu.wav", b"RIFFTRUNCATED", "audio/wav", 415),
    ("AUD-09", "Extension fausse (PNG renommé en WAV)", "faux.wav", b"\x89PNG\r\n\x1a\n" + b"\x00"*30, "audio/wav", 415),
    ("AUD-10", "Format non supporté (FLAC)", "musique.flac", b"fLaC" + b"\x00"*30, "audio/flac", 415),
    ("AUD-11", "Fichier dépassant limite taille (10 Mo)", "trop_lourd.wav", b"RIFF" + struct.pack("<I", MAX_AUDIO_SIZE_BYTES) + b"WAVE" + b"\x00" * (MAX_AUDIO_SIZE_BYTES + 10), "audio/wav", 413),
]

for tid, desc, nom, contenu, mime, attendu in tests_audios:
    t0 = time.perf_counter()
    r = client.post("/multimedia/upload-audio", files={"fichier": (nom, io.BytesIO(contenu), mime)})
    lat = round((time.perf_counter() - t0) * 1000, 2)
    statut = "PASS" if r.status_code == attendu else "FAIL"
    resultats_mm.append((tid, desc, attendu, r.status_code, lat, statut))
    print(f"[{tid}] {desc:<45} | Attendu: {attendu} | Obtenu: {r.status_code} ({lat} ms) -> {statut}")

total_mm = len(resultats_mm)
reussis_mm = sum(1 for r in resultats_mm if r[5] == "PASS")
print(f"\nTotal Multimédia : {reussis_mm}/{total_mm} réussis ({reussis_mm/total_mm*100:.1f}%)")
