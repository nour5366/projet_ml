# Étape 1 — Le projet et le contrat d'API

**Durée : 45 min · Modèle : atelier 1**
**Objectif :** avoir une API qui répond avec un contrat clair, sans dépendre d'un fournisseur.

## À retenir

Un **contrat d'API** est comme le menu d'un restaurant : il dit ce qu'on peut commander (entrée)
et ce qu'on recevra (sortie), sans dire qui fait la cuisine. Si demain on change de cuisinier
(de fournisseur), le menu reste le même : les clients n'ont rien à changer.
On l'écrit **avant** le code, avec Pydantic, et il ne cite aucun fournisseur.

## Les fichiers de cette étape

| Fichier | Rôle |
|---|---|
| `app/schemas.py` | le contrat : `AssistantRequest`, `AssistantResponse` |
| `app/config.py` | lit le fichier `.env` |
| `app/providers.py` | `MockProvider` et `GroqProvider`, avec la même méthode `appeler` |
| `app/main.py` | `GET /health` et `POST /assistant` |
| `tests/test_api.py` | les tests 200, 422, 503 |

Lisez d'abord `schemas.py`. Le cœur du contrat tient en deux lignes :

```python
class AssistantRequest(BaseModel):
    message: str = Field(min_length=3, max_length=500)   # trop court ou trop long -> 422
```

Dans `providers.py`, deux classes ont la même méthode. Le reste du code ne sait pas laquelle
répond. Remarquez que `from groq import Groq` est écrit **dans** la classe `GroqProvider` :
en mode MOCK, la bibliothèque n'est même pas nécessaire.

## Les commandes

Linux : `source .venv/bin/activate` · PowerShell : `.venv\Scripts\Activate.ps1`

```bash
pytest tests/test_api.py -q
uvicorn app.main:app --reload
```

Sortie attendue du premier test : `9 passed`. Puis, dans un autre terminal :

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","mode":"mock","provider":"mock","degrade":false}
```

Ouvrez aussi http://127.0.0.1:8000/docs et envoyez un message de 2 lettres : vous obtenez un **422**.

## 422 contre 503

- **422** : la faute vient du **client** (message invalide). Inutile de réessayer tel quel.
- **503** : la faute vient du **service** (fournisseur en panne). Le client peut réessayer plus tard.
  Le message reste générique : le détail technique (adresse interne, clé) ne sort jamais.

Pour voir un 503 : `SIMULER_PANNE=1` dans `.env`, relancez le serveur, envoyez une demande.

## Point de contrôle

- [ ] `pytest tests/test_api.py -q` est vert.
- [ ] `/health` répond `"provider": "mock"`.
- [ ] Un message de 2 lettres donne 422 et la panne simulée donne 503.

## Erreurs fréquentes

| Symptôme | Cause | Que faire |
|---|---|---|
| `ModuleNotFoundError: fastapi` | venv non activé ou paquets non installés | Activez le venv puis `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError: app` | commande lancée hors du dossier `inscription-sport/` | `cd inscription-sport` puis relancez |
| `Address already in use` (port 8000) | un autre serveur tourne déjà | Arrêtez-le (Ctrl+C) ou ajoutez `--port 8001` |
| 422 « String should have at least 3 characters » | message trop court | Ce n'est pas un bug : c'est le contrat qui fonctionne |
| PowerShell refuse `Activate.ps1` | politique d'exécution | `Set-ExecutionPolicy -Scope Process Bypass` |
| `degrade: true` dans `/health` | `INFERENCE_MODE=real` sans clé : repli sur le mock | Normal : le repli est visible exprès. Remettez `mock` ou ajoutez une clé |

## Ce que je dois savoir expliquer

1. **Pourquoi `schemas.py` ne contient-il aucun nom de fournisseur ?**
   Pour changer de fournisseur sans toucher au contrat : seuls `providers.py` et `config.py` changent.
2. **Quelle différence entre 422 et 503 ?**
   422 : requête invalide (faute du client). 503 : service indisponible (le client peut réessayer).

*Dites « OK » quand le point de contrôle est validé, puis passez à l'étape 2.*
