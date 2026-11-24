# Guide du Bonus Multimédia — SportsAI

## 1. Vue d'ensemble

Le module multimédia de **SportsAI** permet à l'utilisateur de soumettre des images (affiches, bannières, logos de tournois) ou des fichiers audio (demandes vocales d'inscription ou questions).

Le système analyse le contenu, en extrait les informations textuelles exploitables, et les achemine vers le pipeline de traitement de l'agent intelligent.

---

## 2. Architecture de Validation (HTTP 413 & 415)

Pour garantir la sécurité et la robustesse de l'API, chaque fichier entrant traverse un sas de validation strict en **4 niveaux successifs** avant tout appel d'inférence ou modèle d'IA :

```
Requête cliente
      │
      ▼
[1. Vérification de la Taille] ─────────> Trop grand ? ──> HTTP 413 (Payload Too Large)
      │
      ▼
[2. Vérification MIME déclaré] ─────────> Non autorisé ? ──> HTTP 415 (Unsupported Media Type)
      │
      ▼
[3. Signatures Binaires (Magic Bytes)] ──> Incohérent ? ───> HTTP 415 (Unsupported Media Type)
      │
      ▼
[4. Décodage réel (Pillow / pydub)] ────> Corrompu ? ─────> HTTP 415 (Unsupported Media Type)
      │
      ▼
[Analyse Gemini / Simulateur]
```

### Formats et limites

| Type | Formats acceptés | Limite de taille | Signatures binaires (Magic Bytes) |
|---|---|---|---|
| **Image** | JPEG, PNG, WEBP | **5 Mo** | `\xFF\xD8\xFF` (JPEG), `\x89PNG\r\n\x1a\n` (PNG), `RIFF....WEBP` (WEBP) |
| **Audio** | WAV, MP3, M4A, OGG | **10 Mo** | `RIFF....WAVE` (WAV), `ID3` ou sync `\xFF\xFB` (MP3), `ftyp` (M4A), `OggS` (OGG) |

---

## 3. Routes de l'API

### A. Téléverser une image
- **Endpoint** : `POST /multimedia/upload-image`
- **Content-Type** : `multipart/form-data`
- **Paramètre** : `fichier` (UploadFile)
- **Exemple de réponse (200 OK)** :
```json
{
  "media_type": "image",
  "format_detecte": "jpeg",
  "taille_octets": 1024,
  "texte_extrait": "[Image simulée – affiche JPEG d'un marathon de Paris. On y lit : 'Marathon de Paris – 12 avril 2026 – inscriptions ouvertes'. Sport détecté : course à pied.",
  "confiance": 1.0,
  "mode": "simule",
  "metadata": {
    "simulation": true
  }
}
```

### B. Téléverser un audio
- **Endpoint** : `POST /multimedia/upload-audio`
- **Content-Type** : `multipart/form-data`
- **Paramètre** : `fichier` (UploadFile)
- **Exemple de réponse (200 OK)** :
```json
{
  "media_type": "audio",
  "format_detecte": "wav",
  "taille_octets": 2048,
  "texte_extrait": "[Audio simulé – fichier WAV. Transcription : 'Bonjour, je voudrais m'inscrire au tournoi de tennis E05, j'ai 28 ans et je m'appelle Dupont.' Sport détecté : tennis.",
  "confiance": 1.0,
  "mode": "simule",
  "metadata": {
    "simulation": true
  }
}
```

---

## 4. Modes Réel vs Simulé

Le module respecte le principe d'évaluation déterministe et reproductible :
- **Mode Simulé (`INFERENCE_MODE=mock` ou sans clé)** :
  - Renvoie des transcriptions et descriptions fixes, précises et déterministes.
  - Aucune hallucination, aucun appel réseau, idéal pour les tests automatisés et l'évaluation sans quota.
- **Mode Réel (`INFERENCE_MODE=real` + `GEMINI_API_KEY`)** :
  - Fait appel à l'API multimodale Google Gemini (`gemini-2.0-flash`).
  - Si l'appel distant échoue ou si le quota est épuisé, le service se replie automatiquement sur le simulateur avec le tag `"simule_repli"`, assurant une haute disponibilité sans crash serveur.

---

## 5. Exécution des Tests

Pour exécuter l'ensemble des tests du projet (y compris les 20 tests multimédia) :
```bash
pytest tests/ -v
```
Résultat : **87 tests réussis, 0 échec.**
