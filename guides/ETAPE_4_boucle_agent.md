# Étape 4 — La boucle de l'agent

**Durée : 1 h 15 · Modèle : atelier 5 (deuxième moitié)**
**Objectif :** faire utiliser les outils par un agent, avec une boucle limitée et un garde-fou dans le code.

## À retenir

Un agent, c'est un LLM + des outils + une **boucle**. On demande au modèle ; s'il réclame un outil,
on l'exécute et on lui renvoie le résultat ; on recommence jusqu'à ce qu'il réponde en texte.
Image : un stagiaire qui revient chaque fois vous poser une question, jusqu'à ce qu'il ait de quoi rédiger.

```
 demande
   │
   ▼
 ┌─────┐  « appelle l'outil X »   ┌────────────────────┐
 │ LLM │ ───────────────────────▶ │ NOTRE code exécute │
 │     │ ◀─────────────────────── │ l'outil X          │
 └─────┘  résultat + tool_call_id └────────────────────┘
   │  (on recommence, 5 tours au maximum)
   ▼
 réponse en texte
```

## Les fichiers de cette étape

| Fichier | Rôle |
|---|---|
| `app/agent.py` | `executer_agent()` : la boucle, le garde-fou |
| `app/mock_llm.py` | le **faux modèle** déterministe qui appelle les mêmes outils |
| `app/service.py` | relie l'agent à l'API et décide du statut final |
| `tests/test_agent.py` | les tests de cette étape |

La boucle (extrait de `agent.py`) :

```python
for tour in range(1, max_tours + 1):
    msg = fournisseur.appeler(messages, schemas)
    if not msg.tool_calls:                    # du texte : c'est fini
        return {"reponse": msg.content, "appels": appels, "tours": tour, "abandon": False}
    messages.append(message_assistant(msg))   # la demande du modèle, AVANT les résultats
    for appel in msg.tool_calls:
        ...                                   # exécuter l'outil
        messages.append({"role": "tool", "tool_call_id": appel.id, "content": ...})
return {"reponse": "", "appels": appels, "tours": max_tours, "abandon": True}
```

Trois détails qui comptent :
- **`tool_call_id`** relie chaque résultat à la demande qui l'a provoqué ; sans lui, le modèle ne sait pas quel résultat répond à quelle demande.
- **`max_tours`** empêche une boucle sans fin qui viderait votre quota. Au-delà : `abandon=True` et envoi en revue humaine.
- **Arguments JSON cassés** : traités comme `{}` ; `executer_outil` répond alors une erreur lisible.

**Le garde-fou est dans le code**, pas seulement dans la consigne : `executer_outil_garde()` refuse
`creer_inscription` si le message de l'utilisateur ne contient pas une demande explicite
(« inscris-moi », « je veux m'inscrire »). Une simple question n'inscrit jamais personne.

## Le mode MOCK

`mock_llm.py` simule un modèle avec des règles. **Ce n'est pas un vrai modèle.** Il sert à tester
la boucle hors ligne, de façon reproductible. Pour voir le fonctionnement :

```bash
pytest tests/test_agent.py -q
python mesures/essayer.py "Je veux m'inscrire au volley. J'ai 19 ans, je m'appelle Nour."
python mesures/essayer.py "Puis-je m'inscrire au volley ? J'ai 19 ans."
```

Première demande : 3 outils (`lister_evenements`, `verifier_eligibilite`, `creer_inscription`), `statut=inscrit`.
Deuxième : seulement la vérification, **aucune inscription** (c'est une question).

## Point de contrôle

- [ ] `pytest tests/test_agent.py -q` est vert.
- [ ] La question « Puis-je m'inscrire… ? » ne crée aucune inscription.
- [ ] Vous savez expliquer le rôle de `tool_call_id` et de `max_tours`.

## Bonus facultatif : brancher un vrai modèle (Groq)

Nécessite un compte et une clé Groq (gratuit). Rien n'est obligatoire pour la suite.

```bash
python -m pip install -r requirements-reel.txt
```
Dans `.env` : `INFERENCE_MODE=real`, `GROQ_API_KEY=gsk_...`, `MODEL_ID=qwen/qwen3.8-27b`.
Vérifiez `/health` : `provider` doit valoir `groq` et `degrade` doit valoir `false`.
Le code attend 2,1 s entre deux appels (limite de 30 requêtes par minute) et réessaie une fois en cas de quota atteint.
Sans clé valide, l'application retombe sur le mock **et le signale** par `degrade: true`.

## Erreurs fréquentes

| Symptôme | Cause | Que faire |
|---|---|---|
| Erreur 400 du fournisseur sur un message `tool` | le message assistant n'a pas été ajouté **avant** les résultats | Vérifiez l'ordre dans `agent.py` : assistant puis tool |
| `abandon: true` à chaque demande | le modèle redemande toujours un outil | Lisez `actions` dans la réponse : quel outil boucle ? Précisez sa description |
| Une inscription apparaît alors que c'était une question | garde-fou contourné ou `demande_explicite` incorrecte | `pytest tests/test_agent.py` doit rester vert ; ne retirez jamais `executer_outil_garde` |
| `degrade: true` en mode réel | clé absente, invalide ou quota dépassé | Vérifiez `.env` ; le mock a pris le relais |
| Le script lancé tourne trop longtemps en mode réel | pauses de quota | Normal : environ 2 s par appel, comptez 3 à 5 minutes pour 20 demandes |

## Ce que je dois savoir expliquer

1. **À quoi sert `tool_call_id` ?**
   À relier le résultat d'un outil à la demande précise du modèle qui l'a provoqué.
2. **Pourquoi le garde-fou est-il dans le code et pas seulement dans la consigne ?**
   Parce qu'un modèle peut ignorer ou mal interpréter une consigne ; le code, lui, bloque à chaque fois.

*Dites « OK » quand le point de contrôle est validé, puis passez à l'étape 5.*
