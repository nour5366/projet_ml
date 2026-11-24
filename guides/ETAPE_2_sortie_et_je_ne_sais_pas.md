# Étape 2 — Contraindre la sortie et savoir dire « je ne sais pas »

**Durée : 1 h · Modèle : atelier 2**
**Objectif :** que le code décide à la place du modèle, et qu'une demande douteuse soit envoyée à un humain.

## À retenir

Une **énumération** (`Enum`) est un menu déroulant : on choisit parmi une liste fermée, on ne peut
pas inventer une valeur. Une **règle métier** est un videur à l'entrée : il applique toujours la
même règle, quoi que dise le modèle. Et un modèle **répond toujours**, même quand il ne sait pas :
c'est donc à notre code de repérer l'incertitude, avec un **score de confiance** et un **seuil**.

## Les fichiers de cette étape

| Fichier | Rôle |
|---|---|
| `app/schemas.py` | `Sport`, `Intention`, `Statut` (énumérations) et les bornes (âge 5 à 99, id `E\d{2}`) |
| `app/regles.py` | 4 règles : date limite, événement complet, âge hors tranche, doublon |
| `app/analyse.py` | intention, âge, nom, score de confiance, refus explicites |
| `app/service.py` | décide du statut et de `requires_review` |
| `tests/test_regles.py` | les tests de cette étape |

Les règles sont ordinaires et courtes (`app/regles.py`) :

```python
if evenement["places"] <= 0:
    return False, "l'événement est complet (plus aucune place)."
if not evenement["age_min"] <= age <= evenement["age_max"]:
    return False, f"l'âge ({age} ans) est hors de la tranche ..."
```

Le score de confiance part de 0.95 et perd des points pour chaque information manquante
(événement, âge, nom). Dans `service.py` : `requires_review = confiance < REVIEW_THRESHOLD`.

Trois demandes sont **refusées par le code**, sans même appeler le modèle : hors sujet,
inscrire un tiers (« inscris mon ami… »), demander les données d'un autre participant.

## Les commandes

```bash
pytest tests/test_regles.py -q
python mesures/essayer.py "Inscris-moi à un tournoi, j'ai 20 ans."
python mesures/essayer.py "Inscris-moi à la course E04, j'ai 30 ans, je m'appelle Yacine."
python mesures/essayer.py "Inscris mon ami Karim au basket, il a 17 ans."
```

Sortie attendue de la première : `confiance : 0.2`, `statut=a_verifier`, `requires_review=True`.
La deuxième : refus car l'événement est **complet** (c'est la règle, pas le modèle). La troisième : refus « tiers ».

## Pourquoi un modèle répond toujours

Un modèle de langage prédit la suite la plus probable d'un texte. Il n'a pas de bouton « je ne
sais pas » : face à une demande incomplète, il produit quand même une réponse qui a l'air sûre.
Voilà pourquoi on calcule la confiance **nous-mêmes**, avec des règles vérifiables, et qu'on
envoie en revue humaine ce qui est incertain. Le seuil se choisit sur des mesures (étape 5).

## Point de contrôle

- [ ] `pytest tests/test_regles.py -q` est vert.
- [ ] « Inscris-moi à un tournoi, j'ai 20 ans. » donne `requires_review=True`.
- [ ] Une inscription à un événement complet est refusée par la règle, pas par le modèle.

## Erreurs fréquentes

| Symptôme | Cause | Que faire |
|---|---|---|
| `ValueError: 'cricket' is not a valid Sport` | valeur hors de l'énumération | C'est voulu : la liste est fermée. Ajoutez le sport dans `Sport` si besoin |
| 422 sur un âge de 150 ans | borne Pydantic (5 à 99) | Normal. Le mock traite aussi un âge absurde comme « manquant » |
| Une question (« Puis-je m'inscrire… ? ») a inscrit quelqu'un | confusion question / demande | Vérifiez `demande_explicite()` dans `analyse.py` et lancez `pytest` |
| `requires_review` reste `False` malgré un champ manquant | seuil trop bas dans `.env` | Remettez `REVIEW_THRESHOLD=0.60` (voir l'étape 5) |
| Test qui échoue après modification des données | les données de départ ont changé | Vérifiez `data/*.json` : les tests supposent 6 événements et 2 inscriptions |

## Ce que je dois savoir expliquer

1. **Pourquoi les règles métier sont-elles dans le code et pas dans la consigne du modèle ?**
   Une consigne est une demande polie que le modèle peut ignorer ; une règle en Python s'applique à chaque fois.
2. **À quoi sert `requires_review` ?**
   À signaler qu'un humain doit regarder : information manquante, ambiguïté, confiance sous le seuil, agent qui abandonne.

*Dites « OK » quand le point de contrôle est validé, puis passez à l'étape 3.*
