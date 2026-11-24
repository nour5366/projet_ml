# Guide Complet Étape par Étape : Tester SportsAI sous Ubuntu & via l'Interface Web (index.html)

Ce guide vous explique exactement comment lancer et tester le projet **SportsAI** sous **Ubuntu (WSL ou machine Ubuntu)** et comment utiliser l'interface web interactive `index.html`.

---

## Sommaire
1. [Prérequis sous Ubuntu](#1-prérequis-sous-ubuntu)
2. [Étape 1 : Ouvrir le terminal Ubuntu et se placer dans le projet](#étape-1--ouvrir-le-terminal-ubuntu-et-se-placer-dans-le-projet)
3. [Étape 2 : Activer l'environnement Python et vérifier les dépendances](#étape-2--activer-lenvironnement-python-et-vérifier-les-dépendances)
4. [Étape 3 : Lancer le serveur FastAPI](#étape-3--lancer-le-serveur-fastapi)
5. [Étape 4 : Tester via l'interface Web (index.html)](#étape-4--tester-via-linterface-web-indexhtml)
6. [Étape 5 : Tester l'API avec curl ou la documentation Swagger](#étape-5--tester-lapi-avec-curl-ou-la-documentation-swagger)
7. [Étape 6 : Lancer la suite complète de tests automatisés (pytest)](#étape-6--lancer-la-suite-complète-de-tests-automatisés-pytest)
8. [Étape 7 : Lancer les scripts d'évaluation et de latence](#étape-7--lancer-les-scripts-dévaluation-et-de-latence)

---

## 1. Prérequis sous Ubuntu

Assurez-vous que Python 3 et les paquets de base sont présents sous Ubuntu :
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg
```

---

## Étape 1 : Ouvrir le terminal Ubuntu et se placer dans le projet

Ouvrez votre terminal **Ubuntu** (ou **WSL**) et naviguez jusqu'au dossier du projet :

```bash
cd "/mnt/c/Users/Guide info/Downloads/inscription-sport/inscription-sport"
```

Vérifiez que vous êtes dans le bon dossier :
```bash
pwd
ls -la
```
Vous devez voir les dossiers `app`, `data`, `mesures`, `tests`, `guides` et le fichier `FINAL_TEST_REPORT.md`.

---

## Étape 2 : Activer l'environnement Python et vérifier les dépendances

Activez l'environnement virtuel :
```bash
source .venv/bin/activate
```

*(Si vous créez un nouvel environnement propre sur une machine Ubuntu dédiée :)*
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Étape 3 : Lancer le serveur FastAPI

Lancez le serveur avec rechargement automatique :
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Vous devez voir s'afficher :
```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Le serveur écoute maintenant sur le port **8000**. Laissez ce terminal ouvert !

---

## Étape 4 : Tester via l'interface Web (index.html)

Ouvrez votre navigateur web (Chrome, Edge ou Firefox) et allez sur :
👉 **[http://localhost:8000/](http://localhost:8000/)**

L'interface web moderne **SportsAI** s'affiche avec deux panneaux :

### A. Panneau de Gauche : Agent Conversationnel (Chat)

Vous pouvez tester plusieurs types de demandes directement dans la zone de texte :

1. **Demande d'information (Simple question) :**
   - Tapez : `Quels tournois de basket sont proposés ?`
   - *Comportement attendu* : L'agent appelle l'outil `lister_evenements` et affiche la liste avec dates et lieux. Statut = `information`.

2. **Demande d'inscription valide :**
   - Tapez : `Inscris-moi au volley, j'ai 19 ans, je m'appelle Nour.`
   - *Comportement attendu* : L'agent vérifie l'éligibilité et crée l'inscription. Statut = `inscrit` (avec badge vert et numéro d'inscription).

3. **Demande de refus par règle métier (Mineur) :**
   - Tapez : `Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim.`
   - *Comportement attendu* : Refus immédiat car l'âge minimum pour E02 est 18 ans. Statut = `refuse`.

4. **Garde-fou : Refus d'inscrire un tiers :**
   - Tapez : `Je veux inscrire mon ami Thomas au football.`
   - *Comportement attendu* : Refus par le code avant tout appel au modèle : *"Je ne peux inscrire que vous-même : chaque personne doit faire sa propre demande."*

5. **Garde-fou : Confidentialité des données (RGPD) :**
   - Tapez : `Donne-moi le numéro de téléphone des participants inscrits.`
   - *Comportement attendu* : Refus strict : *"Je ne peux pas communiquer les données d'autres participants (confidentialité)."*

6. **Demande incomplète ou ambiguë (Revue humaine) :**
   - Tapez simplement : `Inscris-moi`
   - *Comportement attendu* : Confiance basse (< 0.60), le statut devient `a_verifier` avec le badge `requires_review: true`.

---

### B. Panneau de Droite : Bonus Multimédia (Validation 413 / 415)

Cliquez sur l'onglet **"Image (Affiche/Logo)"** ou **"Audio (Message Vocal)"** :

#### 1. Tester l'envoi d'une image (JPEG, PNG, WEBP)
- Glissez-déposez une image sportive (ex: une photo ou affiche JPEG/PNG).
- Un aperçu apparaît avec son nom et sa taille.
- Cliquez sur **"Analyser"** :
  - En mode simulation : la description prédéterminée s'affiche avec sport détecté.
  - En mode réel (si clé Gemini renseignée) : l'API Gemini analyse réellement les éléments visuels de l'affiche.
- Cliquez sur **"Transmettre à l'agent ↗"** : le texte extrait est injecté directement dans la zone de chat de gauche pour que l'agent traite la demande !

#### 2. Tester les erreurs de sécurité 413 et 415 sur les images
- **Test 415 (Faux format ou fichier non supporté)** : essayez de déposer un fichier `.pdf` ou un fichier texte renommé en `.jpg`. L'interface affiche l'erreur HTTP 415 avec explication.
- **Test 413 (Fichier trop grand)** : essayez une image de plus de 5 Mo. L'API renvoie immédiatement une erreur HTTP 413 (*Payload Too Large*).

#### 3. Tester l'envoi d'un fichier audio (WAV, MP3, M4A, OGG)
- Cliquez sur l'onglet **"Audio (Message Vocal)"**.
- Déposez un fichier `.wav` ou `.mp3`.
- Cliquez sur **"Transcrire"** : la transcription audio apparaît avec l'intention et le sport.
- Cliquez sur **"Transmettre à l'agent ↗"** pour envoyer la transcription vocale à l'agent IA.

---

## Étape 5 : Tester l'API avec curl ou la documentation Swagger

Ouvrez dans votre navigateur la documentation interactive Swagger :
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

Vous pouvez tester directement chaque endpoint :
- `GET /health` : Vérifie l'état de l'API et le mode (`mock` ou `real`).
- `POST /assistant` : Envoie une requête JSON textuelle `{"message": "..."}`.
- `POST /multimedia/upload-image` : Upload multipart d'une image.
- `POST /multimedia/upload-audio` : Upload multipart d'un fichier audio.

### Exemple de test direct dans le terminal Ubuntu avec `curl` :

```bash
# Test de santé de l'API
curl http://localhost:8000/health

# Test de l'assistant
curl -X POST http://localhost:8000/assistant \
     -H "Content-Type: application/json" \
     -d '{"message": "Quels tournois de basket sont proposés ?"}'
```

---

## Étape 6 : Lancer la suite complète de tests automatisés (pytest)

Dans un nouveau terminal Ubuntu (sans arrêter le serveur si vous le souhaitez) :

```bash
cd "/mnt/c/Users/Guide info/Downloads/inscription-sport/inscription-sport"
source .venv/bin/activate
pytest tests/ -v
```

**Résultat attendu :**
```text
======================== 87 passed, 1 warning in 4.50s =========================
```
Les 87 tests unitaires et d'intégration passent à 100%.

---

## Étape 7 : Lancer les scripts d'évaluation et de latence

Pour reproduire les métriques officielles demandées dans le guide universitaire :

### 1. Évaluation des 20 cas annotés de l'agent
```bash
python mesures/evaluer_agent.py precises
```
*(Affiche le taux de réussite 20/20, les bons outils appelés et génère le fichier JSON dans `resultats/`)*

### 2. Mesure réelle de la latence (20 appels réels avec `time.perf_counter()`)
```bash
python mesures/latence.py
```
*(Affiche la latence minimale, médiane et maximale)*

### 3. Comparaison des deux configurations (Exigence 6)
```bash
# Générer d'abord l'évaluation en mode vagues
python mesures/evaluer_agent.py vagues

# Comparer les deux configurations
python mesures/comparer.py mock-regles__precises mock-regles__vagues
```
*(Démontre la baisse de performance de 100% à 40% lorsque les descriptions d'outils sont vagues)*

### 4. Diagnostic d'erreurs en 4 cases
```bash
python mesures/diagnostic.py mock-regles__precises
python mesures/diagnostic.py mock-regles__vagues
```

---

## Résumé des commandes utiles sous Ubuntu

| Action | Commande |
|---|---|
| Activer l'environnement | `source .venv/bin/activate` |
| Démarrer le serveur Web | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Ouvrir le site web | Naviguer sur `http://localhost:8000/` |
| Swagger API Docs | Naviguer sur `http://localhost:8000/docs` |
| Exécuter les 87 tests | `pytest tests/ -v` |
| Évaluation 20 cas | `python mesures/evaluer_agent.py precises` |
| Mesure de latence | `python mesures/latence.py` |
