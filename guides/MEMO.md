# Mémo — commandes, repères, vocabulaire

## Commandes

| Action | Linux / macOS | Windows PowerShell |
|---|---|---|
| Créer le venv | `python3 -m venv .venv` | `python -m venv .venv` |
| Activer | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| Installer | `python -m pip install -r requirements.txt` | idem |
| Copier la config | `cp .env.example .env` | `copy .env.example .env` |
| Tests | `pytest -q` | idem |
| Serveur | `uvicorn app.main:app --reload` | idem |
| Santé | `curl http://127.0.0.1:8000/health` | `Invoke-RestMethod http://127.0.0.1:8000/health` |
| Variable temporaire | `INFERENCE_MODE=real python ...` | `$env:INFERENCE_MODE="real"` |
| Essayer | `python mesures/essayer.py "..."` | idem |
| Évaluer | `python mesures/evaluer_agent.py [vagues] [modèle]` | idem |
| Comparer | `python mesures/comparer.py` | idem |
| Diagnostic | `python mesures/diagnostic.py <étiquette>` | idem |
| Seuil | `python mesures/seuil.py` | idem |
| Latence | `python mesures/latence.py` | idem |

Toutes les commandes se lancent depuis le dossier `inscription-sport/`, venv activé.

## Repères

| Code | Signification |
|---|---|
| 200 | tout va bien |
| 422 | requête invalide : faute du client |
| 503 | service indisponible : réessayer plus tard |
| `degrade: true` | le mode réel a échoué, le mock a répondu |
| `requires_review: true` | un humain doit regarder |
| `abandon: true` | `max_tours` atteint |

Valeurs de départ : `REVIEW_THRESHOLD=0.60` · `max_tours=5` · âge 5 à 99 · 30 requêtes par minute chez Groq.

## Vocabulaire

- **Contrat d'API** : ce que l'API accepte et renvoie, écrit indépendamment de qui fait le travail.
- **Pydantic** : bibliothèque qui vérifie les types et les bornes des données.
- **Énumération (Enum)** : liste fermée de valeurs permises.
- **Règle métier** : décision écrite en code, qui ne dépend pas du modèle.
- **Mock** : simulateur hors ligne qui remplace le vrai fournisseur pour les tests.
- **Fournisseur (provider)** : le service qui exécute le modèle.
- **Outil (tool)** : fonction que le modèle peut demander ; c'est notre code qui l'exécute.
- **JSON Schema** : format qui décrit un outil et ses paramètres au modèle.
- **Agent** : LLM + outils + boucle.
- **`tool_call_id`** : identifiant qui relie un résultat à la demande d'outil correspondante.
- **`max_tours`** : nombre maximal d'allers-retours avec le modèle.
- **Garde-fou** : vérification dans le code qui bloque une action non autorisée.
- **Score de confiance** : note entre 0 et 1 qui dit à quel point la demande est complète et claire.
- **Seuil** : valeur de confiance en dessous de laquelle on envoie en revue humaine.
- **Faux négatif / faux positif** : demande à revoir non revue / demande revue pour rien.
- **Jeu de test annoté** : demandes avec la bonne réponse attendue, écrite à l'avance.
- **Médiane** : valeur du milieu ; plus représentative que la moyenne quand quelques valeurs sont extrêmes.
