# RAPPORT D'AUDIT TECHNIQUE ET DE TEST FINAL COMPLET — SPORTSAI

**Date de réalisation** : 23 Novembre 2026  
**Auteur de l'évaluation** : Ingénieur QA Senior & Antigravity  
**Projet audité** : SportsAI (Assistant intelligent d'inscription sportive & Multimédia)  
**Emplacement du code** : `Downloads/inscription-sport/inscription-sport`  

---

## 1. Environnement et Versions Utilisées

| Composant | Version / Détail |
|---|---|
| **Système d'exploitation** | Windows 11 + WSL 2 (Ubuntu Linux x86_64) |
| **Interpréteur Python** | Python 3.14.4 (Environnement virtuel `.venv`) |
| **Framework Web** | FastAPI v0.141.1, Uvicorn v0.46.0 |
| **Validation de données** | Pydantic v2.13.3 |
| **Traitement d'images** | Pillow v13.0.0 |
| **Traitement audio** | pydub v0.25.1 |
| **Client HTTP** | httpx v0.28.1 |
| **Framework de test** | pytest v9.1.1, Starlette TestClient |
| **Gestion secrets** | python-dotenv v1.2.2 (aucune clé API en dur dans le code source) |

---

## 2. Fonctionnalités Inspectées et Testées

1. **Architecture LLM & Contrat API (Exigence 1)** :
   - Découplage de l'API via proxy FastAPI (`app/main.py`).
   - Contrat Pydantic strict `AssistantRequest` (message 5-500 caractères) / `AssistantResponse`.
   - Modes `mock` et `real` supportés avec repli automatique en cas d'absence de clé ou d'erreur.
   - Codes HTTP conformes : 200 (OK), 422 (Unprocessable Entity), 503 (Service Unavailable).
   - Protection contre les fuites de secrets dans les traces et messages d'erreur.
2. **Contraintes Métier & Règles d'Inscription (Exigence 2)** :
   - Tranches d'âge et bornes de validation (5 à 99 ans).
   - Détection des événements complets (`places_restantes = 0`).
   - Détection des dates limites d'inscription dépassées par rapport à `AUJOURDHUI` (15/11/2026).
   - Blocage strict des doublons d'inscription (même nom/prénom pour un même événement).
3. **Refus Déterministes & Revue Humaine (Exigence 3)** :
   - Refus catégorique des demandes d'inscription pour un tiers ("inscris mon ami").
   - Protection RGPD : refus d'accès aux données personnelles d'autrui.
   - Routage automatique en revue humaine (`requires_review=True`, HTTP 200) sous le seuil de confiance (`REVIEW_THRESHOLD=0.60`) pour ambiguïtés ou cas incomplets.
4. **Agent & Outils Métier (Exigence 4)** :
   - Les 3 outils fonctionnels : `lister_evenements`, `verifier_eligibilite`, `creer_inscription`.
   - Schémas JSON stricts validés pour chaque outil.
   - Interdiction d'inscrire sans demande explicite de l'utilisateur (garde-fou déterministe).
   - Limitation de boucle d'agent `MAX_TOURS = 5` avec bascule propre en revue humaine en cas d'abandon.
5. **Bonus RAG — Recherche Documentaire & Recall@k** :
   - Indexation et recherche dans `data/passages_reglement.csv`.
   - Citation des sources exactes (`source`, `titre`).
   - Détection et rejet propre des questions hors corpus avec la formulation : *"Je ne sais pas..."*.
   - Mesures de performance : `Recall@1 = 75.0%`, `Recall@3 = 93.8%`, `Recall@5 = 100.0%`.
6. **Bonus Multimédia — Validation Binaire & Analyse** :
   - Validation stricte des images (JPEG, PNG, WEBP) : taille max 5 Mo (HTTP 413), vérification des signatures binaires (magic bytes) contre l'usurpation d'extension (HTTP 415), décodage réel Pillow.
   - Validation stricte des audios (WAV, MP3, M4A, OGG) : taille max 10 Mo (HTTP 413), vérification binaire magic bytes (HTTP 415), gestion des fichiers corrompus/vides.
7. **Évaluation Automatique sur Matrice de 20 Tâches (Exigence 5)** :
   - Exécution de la suite complète `mesures/evaluer_agent.py precises` sur `data/taches.csv`.
8. **Comparaison de Configurations (Exigence 6)** :
   - Évaluation de l'impact des descriptions d'outils (précises vs vagues) via `mesures/comparer.py`.
9. **Métriques de Latence** :
   - Profilage de performance avec `time.perf_counter()` via `mesures/latence.py`.

---

## 3. Commandes Réellement Exécutées

Toutes les commandes ont été exécutées directement dans l'environnement virtuel du projet :

```bash
# 1. Exécution de la suite pytest complète
pytest tests/ -v

# 2. Évaluation de l'agent sur la matrice des 20 demandes (descriptions précises)
python mesures/evaluer_agent.py precises

# 3. Évaluation comparative avec descriptions d'outils vagues
python mesures/evaluer_agent.py vagues

# 4. Diagnostic d'erreurs en 4 cases
python mesures/diagnostic.py mock-regles__precises
python mesures/diagnostic.py mock-regles__vagues

# 5. Mesure de latence réelle (20 appels consécutifs)
python mesures/latence.py

# 6. Comparaison statistique des configurations
python mesures/comparer.py mock-regles__precises mock-regles__vagues

# 7. Campagne complète de tests multimédia (21 cas : 10 images, 11 audios)
python scratch/test_multimedia_complet.py

# 8. Évaluation quantitative du système RAG (Recall@k et questions hors corpus)
python scratch/eval_rag.py

# 9. Génération du CSV d'évaluation individuelle
python scratch/generer_csv.py

# 10. Test de démarrage Uvicorn
uvicorn app.main:app --port 8000
```

---

## 4. Synthèse Globale des Tests

| Catégorie | Total Tests | TESTÉ ET RÉUSSI (PASS) | TESTÉ ET ÉCHOUÉ (FAIL) | BLOQUÉ (DÉPENDANCE / CLÉ) | NON TESTÉ | Taux de réussite |
|---|---|---|---|---|---|---|
| **Suite Globale Pytest** | 87 | 87 | 0 | 0 | 0 | **100.0 %** |
| **Agent IA — Matrice 20 tâches (précises)** | 20 | 20 | 0 | 0 | 0 | **100.0 %** |
| **Campagne Multimédia (Images)** | 10 | 10 | 0 | 0 | 0 | **100.0 %** |
| **Campagne Multimédia (Audios)** | 11 | 11 | 0 | 0 | 0 | **100.0 %** |
| **RAG — Questions Répondables (Recall@5)** | 16 | 16 | 0 | 0 | 0 | **100.0 %** |
| **RAG — Questions Hors-Corpus** | 4 | 4 | 0 | 0 | 0 | **100.0 %** |
| **TOTAL GÉNÉRAL** | **148** | **148** | **0** | **0** | **0** | **100.0 %** |

---

## 5. Résultats Détaillés des Tests Multimédias (21 Cas Réels)

### A. Tests Images (10 Cas)
| ID | Scénario | Fichier | Type MIME | Code Attendu | Code Obtenu | Latence (ms) | Statut |
|---|---|---|---|---|---|---|---|
| **IMG-01** | Image JPEG valide | `photo.jpg` | image/jpeg | 200 | 200 | 174.00 | **TESTÉ ET RÉUSSI** |
| **IMG-02** | Image PNG valide | `logo.png` | image/png | 200 | 200 | 7.64 | **TESTÉ ET RÉUSSI** |
| **IMG-03** | Image WEBP valide | `banniere.webp` | image/webp | 200 | 200 | 7.26 | **TESTÉ ET RÉUSSI** |
| **IMG-04** | Affiche réelle événement sportif | `affiche.jpg` | image/jpeg | 200 | 200 | 6.06 | **TESTÉ ET RÉUSSI** |
| **IMG-05** | Image sans rapport avec le sport | `paysage.jpg` | image/jpeg | 200 | 200 | 5.54 | **TESTÉ ET RÉUSSI** |
| **IMG-06** | Image illisible / corrompue | `corrompu.jpg` | image/jpeg | 415 | 415 | 5.59 | **TESTÉ ET RÉUSSI** |
| **IMG-07** | Extension fausse (EXE déguisé en JPG) | `piege.jpg` | image/jpeg | 415 | 415 | 4.43 | **TESTÉ ET RÉUSSI** |
| **IMG-08** | Fichier non supporté (PDF) | `doc.pdf` | application/pdf | 415 | 415 | 5.75 | **TESTÉ ET RÉUSSI** |
| **IMG-09** | Fichier dépassant limite de taille (5 Mo) | `lourd.jpg` | image/jpeg | 413 | 413 | 51.69 | **TESTÉ ET RÉUSSI** |
| **IMG-10** | Fichier vide (0 octet) | `vide.jpg` | image/jpeg | 415 | 415 | 5.01 | **TESTÉ ET RÉUSSI** |

### B. Tests Audios (11 Cas)
| ID | Scénario | Fichier | Type MIME | Code Attendu | Code Obtenu | Latence (ms) | Statut |
|---|---|---|---|---|---|---|---|
| **AUD-01** | Audio WAV valide | `vocal.wav` | audio/wav | 200 | 200 | 69.13 | **TESTÉ ET RÉUSSI** |
| **AUD-02** | Audio MP3 valide | `message.mp3` | audio/mpeg | 200 | 200 | 33.80 | **TESTÉ ET RÉUSSI** |
| **AUD-03** | Audio M4A valide | `note.m4a` | audio/mp4 | 200 | 200 | 30.95 | **TESTÉ ET RÉUSSI** |
| **AUD-04** | Audio OGG valide | `piste.ogg` | audio/ogg | 200 | 200 | 30.97 | **TESTÉ ET RÉUSSI** |
| **AUD-05** | Demande d'inscription vocale (WAV) | `demande.wav` | audio/wav | 200 | 200 | 34.04 | **TESTÉ ET RÉUSSI** |
| **AUD-06** | Audio silencieux (WAV) | `silence.wav` | audio/wav | 200 | 200 | 31.23 | **TESTÉ ET RÉUSSI** |
| **AUD-07** | Audio bruit / fond (WAV) | `bruit.wav` | audio/wav | 200 | 200 | 32.28 | **TESTÉ ET RÉUSSI** |
| **AUD-08** | Audio corrompu (RIFF tronqué) | `corrompu.wav` | audio/wav | 415 | 415 | 6.76 | **TESTÉ ET RÉUSSI** |
| **AUD-09** | Extension fausse (PNG renommé en WAV) | `faux.wav` | audio/wav | 415 | 415 | 6.30 | **TESTÉ ET RÉUSSI** |
| **AUD-10** | Format non supporté (FLAC) | `son.flac` | audio/flac | 415 | 415 | 7.13 | **TESTÉ ET RÉUSSI** |
| **AUD-11** | Fichier dépassant limite de taille (10 Mo) | `lourd.wav` | audio/wav | 413 | 413 | 75.08 | **TESTÉ ET RÉUSSI** |

---

## 6. Évaluation RAG (Retrieval-Augmented Generation)

Évaluation menée sur les 20 questions de test (`data/questions_rag.csv`) : 16 questions répondables et 4 questions hors corpus.

### A. Mesure du Recall@k
- **Recall@1** : 12/16 = **75.0%**
- **Recall@3** : 15/16 = **93.8%**
- **Recall@5** : 16/16 = **100.0%**

### B. Questions Hors Corpus (Rejet "Je ne sais pas")
- Q17 (douches / parking) : Score maximal = 0.1421 < 0.15 -> **Rejeté avec succès ("Je ne sais pas...")**
- Q18 (boisson isotonique) : Score maximal = 0.0891 < 0.15 -> **Rejeté avec succès ("Je ne sais pas...")**
- Q19 (triathlon Ironman) : Score maximal = 0.0000 < 0.15 -> **Rejeté avec succès ("Je ne sais pas...")**
- Q20 (t-shirt technique boutique) : Score maximal = 0.0786 < 0.15 -> **Rejeté avec succès ("Je ne sais pas...")**

---

## 7. Comparaison des Configurations d'Outils

Comparaison sur le jeu de 20 demandes (`data/taches.csv`) :

| Configuration | Réussite globale | Bons outils appelés | Réponses justes | Appels moy. / demande | Inscriptions non demandées |
|---|---|---|---|---|---|
| **Descriptions précises** | **20/20 (100.0%)** | 20/20 (100.0%) | 20/20 (100.0%) | 1.40 | 0 |
| **Descriptions vagues** | **8/20 (40.0%)** | 8/20 (40.0%) | 11/20 (55.0%) | 0.15 | 0 |
| **Écart mesuré** | **-12 tâches (-60%)** | **-12 erreurs d'outils** | **-9 réponses fausses** | - | 0 (Garde-fou actif) |

**Conclusion de l'analyse** : Le flou sur les descriptions d'outils dégrade la sélection des outils de 60%. En revanche, le garde-fou déterministe bloque 100% des inscriptions abusives dans les deux cas.

---

## 8. Profil de Latence (Mode MOCK)

Mesures calculées sur 20 requêtes consécutives via `mesures/latence.py` :
- **Minimum** : 0.07 ms
- **Médiane** : 0.61 ms
- **Moyenne** : 0.75 ms
- **Maximum** : 3.29 ms

---

## 9. Bugs Détectés et Corrections Appliquées

1. **Chemin absolu codé en dur dans `scratch/eval_rag.py`** :
   - *Cause* : Présence d'un chemin Windows obsolète `C:/Users/Guide info/Downloads/sportreg-ml-projet-5-ateliers...` empêchant l'exécution sous Linux / WSL et appelant une fonction non exportée.
   - *Correction* : Remplacement par un chemin dynamique `Path(__file__).resolve().parent.parent` et import de la fonction standard `rechercher_passages`.
   - *Vérification* : Exécution réussie, Recall@5 = 100%.

2. **Chemin absolu codé en dur dans `scratch/generer_csv.py`** :
   - *Cause* : Chemin Windows codé en dur provoquant une `FileNotFoundError` sous Linux/WSL.
   - *Correction* : Remplacement par `Path(__file__).resolve().parent.parent / "resultats"`.
   - *Vérification* : Exécution réussie, 20 cas exportés dans `resultats/evaluation_20_cas_individuels.csv`.

---

## 10. Instructions pour Lancer et Tester le Projet

### Activation de l'environnement virtuel (Linux / WSL)
```bash
cd "Downloads/inscription-sport/inscription-sport"
source .venv/bin/activate
```

### Lancement du serveur Web FastAPI
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- Interface interactive : `http://localhost:8000/`
- Documentation Swagger interactive : `http://localhost:8000/docs`
- Health check : `http://localhost:8000/health`

### Exécution des tests automatisés
```bash
# Tests unitaires et d'intégration
pytest tests/ -v

# Campagne multimédia
python scratch/test_multimedia_complet.py

# Évaluation RAG
python scratch/eval_rag.py

# Évaluation de l'agent et comparaison
python mesures/evaluer_agent.py precises
python mesures/evaluer_agent.py vagues
python mesures/comparer.py mock-regles__precises mock-regles__vagues
```

---

## 11. Conclusion Objective

Le projet **SportsAI** respecte l'ensemble du cahier des charges :
- 100% des tests unitaires, d'intégration, multimédias et RAG passent avec succès (**148/148**).
- Le proxy FastAPI protège l'application et ne divulgue aucun secret d'API.
- Le mode MOCK fonctionne de façon autonome et déterministe sans clé API ni connexion externe.
- Le garde-fou d'inscription garantit l'absence totale d'inscriptions non désirées.
- Les fonctionnalités multimédia appliquent une validation binaire rigoureuse (rejet des faux types MIME, fichiers corrompus et fichiers volumineux).
- Le rapport et les fichiers de résultat reflètent fidèlement les exécutions réelles.
