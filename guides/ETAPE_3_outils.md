# Étape 3 — Décrire des outils

**Durée : 1 h · Modèle : atelier 5 (première moitié)**
**Objectif :** écrire 3 outils Python et leurs descriptions JSON Schema, sans qu'aucune erreur ne fasse planter le programme.

## À retenir

Le modèle **ne fait rien lui-même** : il ne voit jamais nos données. Il lit la *description* d'un
outil et **choisit** lequel appeler ; c'est **notre code** qui l'exécute. C'est comme un client qui
lit le menu et commande : il ne cuisine pas. Si la description est vague, il commandera le mauvais plat.

## Les fichiers de cette étape

| Fichier | Rôle |
|---|---|
| `app/outils.py` | les 3 fonctions, leurs descriptions (`SCHEMAS`) et `executer_outil()` |
| `tests/test_outils.py` | les tests de cette étape |

Les trois outils :

| Outil | Effet | Quand l'utiliser |
|---|---|---|
| `lister_evenements(sport)` | lecture | l'utilisateur cherche un sport, une date, ce qui est proposé |
| `verifier_eligibilite(id_evenement, age)` | lecture | l'utilisateur donne son âge, ou avant toute inscription |
| `creer_inscription(id_evenement, nom, age)` | **modifie les données** | **UNIQUEMENT** si l'utilisateur le demande explicitement |

Une description en JSON Schema (extrait de `outils.py`) : le nom exact, une phrase qui dit
**QUAND** utiliser l'outil, des paramètres typés et bornés.

```python
schema("creer_inscription",
       "Crée une inscription (seule action qui modifie quelque chose). À utiliser "
       "UNIQUEMENT si l'utilisateur demande explicitement de l'inscrire ...",
       {"id_evenement": ID_EVENEMENT, "nom": NOM, "age": AGE},
       ["id_evenement", "nom", "age"])
```

`executer_outil()` ne plante jamais : une erreur devient un résultat lisible par le modèle.

```python
executer_outil("verifier_eligibilite", {"id_evenement": "E02"})
# -> {"erreur": "arguments invalides (age : Field required)"}
```

## Les commandes

```bash
pytest tests/test_outils.py -q
python -c "from app.outils import executer_outil; print(executer_outil('verifier_eligibilite', {'id_evenement':'E02','age':17}))"
python -c "from app.outils import executer_outil; print(executer_outil('verifier_eligibilite', {'id_evenement':'E02'}))"
```

Sortie attendue du premier : `16 passed`. Deuxième commande : un dictionnaire avec `"eligible": True`.
Troisième : `{'erreur': 'arguments invalides (age : Field required)'}`. Aucun plantage.

## Point de contrôle

- [ ] `pytest tests/test_outils.py -q` est vert.
- [ ] Un argument manquant donne `{"erreur": ...}` au lieu d'un crash.
- [ ] Vous savez dire quel outil est le seul à modifier les données.

## Erreurs fréquentes

| Symptôme | Cause | Que faire |
|---|---|---|
| `{"erreur": "outil inconnu : ..."}` | nom différent entre le schéma et le dictionnaire `OUTILS` | Le nom doit être **exactement** le même |
| `arguments invalides (id_evenement : String should match pattern)` | id mal écrit (`02` au lieu de `E02`) | Format imposé : E suivi de 2 chiffres |
| Le test « chaque outil a un schéma valide » échoue | un `required` cite un paramètre absent de `properties` | Corrigez la liste des paramètres requis |
| Les données changent d'un test à l'autre | une inscription créée reste en mémoire | `conftest.py` appelle `recharger_donnees()` avant chaque test : ne le supprimez pas |
| `ModuleNotFoundError: app` | mauvais dossier | Lancez les commandes depuis `inscription-sport/` |

## Ce que je dois savoir expliquer

1. **Pourquoi le modèle ne peut-il pas « faire » une inscription lui-même ?**
   Il ne voit pas la base et n'exécute rien : il demande un outil, notre code l'exécute après avoir vérifié les arguments.
2. **Pourquoi `executer_outil()` renvoie-t-elle `{"erreur": ...}` au lieu de planter ?**
   Le modèle peut lire l'erreur et corriger son appel ; un crash arrêterait toute la demande.

*Dites « OK » quand le point de contrôle est validé, puis passez à l'étape 4.*
