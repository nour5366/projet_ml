# Étape 5 — Mesurer, comparer, décider

**Durée : 1 h 30 · Modèle : ateliers 2 et 5**
**Objectif :** transformer « ça marche à peu près » en chiffres, comparer UNE variable, justifier votre seuil.

## À retenir

Mesurer, c'est comme corriger un examen : on a des questions (les 20 demandes), la bonne réponse
attendue pour chacune, et une règle de notation écrite à l'avance. Pour comparer deux versions, on
ne change **qu'une seule chose** : sinon on ne sait plus ce qui a produit l'écart.

## Les fichiers de cette étape

| Fichier | Rôle |
|---|---|
| `data/taches.csv` | 20 demandes annotées : normales, difficiles (SMS, sans accents, ambiguës) et à refuser |
| `mesures/metriques.py` | les métriques écrites à la main |
| `mesures/evaluer_agent.py` | lance les 20 demandes et calcule les scores |
| `mesures/comparer.py` | tableau comparatif et écart en **nombre de demandes** |
| `mesures/diagnostic.py` | tableau 2×2 : où est l'échec ? |
| `mesures/seuil.py` | choisir `REVIEW_THRESHOLD` par les mesures |
| `mesures/latence.py` | bonus : minimum, médiane, maximum sur 20 appels |
| `tests/test_mesures.py` | tests de cette étape |

## Les métriques, avec un exemple chiffré

| Mesure | Question | Exemple |
|---|---|---|
| **bons outils** | A-t-il appelé exactement les outils attendus ? Aucun, quand il ne fallait rien appeler. Lister les événements est une lecture sans effet : tolérée si `consultation_toleree=1` | attendu `[verifier_eligibilite]`, appelé `[lister_evenements, verifier_eligibilite]` : correct (consultation tolérée) |
| **réponses justes** | La réponse contient-elle tous les faits attendus ? | faits `tranche` : « l'âge (25 ans) est hors de la tranche 12-17 ans » : juste |
| **tâches réussies** | Les deux à la fois : c'est le score de décision | 14 réussies sur 20 = 0,70 |
| **appels par demande** | Combien d'outils appelés en moyenne ? | 28 appels pour 20 demandes = 1,4 |
| **inscriptions non demandées** | Inscriptions réellement créées sans demande : une faute, même si la réponse est juste | doit toujours valoir **0** |
| **abandons** | `max_tours` atteint | doit valoir 0 |

## Les commandes

```bash
pytest -q                                   # tout doit rester vert
python mesures/evaluer_agent.py             # variante PRECISES
python mesures/evaluer_agent.py vagues      # variante VAGUES : une seule chose change
python mesures/comparer.py
python mesures/diagnostic.py mock-regles__vagues
python mesures/seuil.py
python mesures/latence.py
```

## Comparer en changeant UNE variable

Variable choisie : **la description des outils**. Même agent, mêmes 20 demandes, mêmes données.
La variante `vagues` remplace chaque description par le simple nom de l'outil et retire la
description des paramètres (`vaguer()` dans `outils.py`).

Écart exprimé en **nombre de demandes** : 1 demande sur 20 = **5 points**. On ne déclare une
différence qu'à partir de **3 demandes d'écart** ; en dessous, c'est peut-être du hasard.

**Attention à l'honnêteté de vos chiffres.** Avec le mock, l'écart mesuré prouve que votre
protocole fonctionne, pas ce qu'un vrai modèle ferait. Dans ce mode, le simulateur n'appelle un
outil que s'il « comprend » sa description : l'écart est donc construit par le simulateur. Pour la soutenance,
refaites les deux mesures avec un vrai modèle (étape 4, bonus) et notez le fournisseur dans votre fiche.
Pour comparer deux **modèles** : `python mesures/evaluer_agent.py precises openai/gpt-oss-20b`.

## Le diagnostic 2×2

|  | réponse juste | réponse fausse |
|---|---|---|
| **bons outils** | ok | RÉDACTION (résultat mal lu) |
| **mauvais outils** | détour (juste, mais par un autre chemin) | OUTILS (mauvais choix d'outil) |

Beaucoup de cases « OUTILS » : améliorez les **descriptions**. Beaucoup de « RÉDACTION » : améliorez la **consigne**.

## Justifier le seuil `REVIEW_THRESHOLD`

`python mesures/seuil.py` essaie tous les seuils de 0,30 à 0,95 et compte, sur vos 20 demandes :
- **faux négatifs** : une demande qui aurait dû aller en revue mais n'y va pas (le plus grave),
- **faux positifs** : une demande envoyée en revue pour rien (coûte du temps humain).

Il affiche aussi les deux confiances limites. Avec les données fournies : plus haute confiance d'une
demande à revoir = 0,55 ; plus basse confiance d'une demande à ne pas revoir = 0,65 ; tout seuil
entre les deux sépare parfaitement les groupes, et **0,60** est au milieu. Écrivez cette
justification **avec vos propres chiffres** dans `FICHE_PROJET.md`. Si vous ajoutez ou modifiez des demandes, relancez le script.

## Bonus : la latence

`python mesures/latence.py` donne minimum, médiane et maximum sur 20 appels. La **moyenne seule est
trompeuse** : un seul appel très lent (réseau saturé, quota atteint) la tire vers le haut alors que
presque tous les appels sont rapides. La médiane dit ce que vit l'utilisateur typique ; le maximum, le pire cas.
En mode MOCK, les durées sont de l'ordre de la fraction de milliseconde : refaites la mesure en mode réel.

## Point de contrôle

- [ ] `pytest -q` est vert.
- [ ] Vous avez lancé les deux variantes et `comparer.py` affiche l'écart en nombre de demandes.
- [ ] Vous pouvez expliquer pourquoi `REVIEW_THRESHOLD` vaut ce qu'il vaut, chiffres à l'appui.
- [ ] `FICHE_PROJET.md` est remplie avec vos résultats.

## Erreurs fréquentes

| Symptôme | Cause | Que faire |
|---|---|---|
| `comparer.py` : « Il faut au moins 2 fichiers » | une seule variante lancée | Lancez `evaluer_agent.py` puis `evaluer_agent.py vagues` |
| `diagnostic.py` : `FileNotFoundError` | étiquette mal écrite | Regardez les noms dans `resultats/` (ex. `mock-regles__vagues`) |
| 20/20 partout et c'est « trop beau » | le mock est conçu pour réussir ce jeu de test | Normal : mesurez avec un vrai modèle et gardez les cas difficiles |
| Écart de 1 ou 2 demandes | trop petit pour conclure | Règle des 3 demandes : ne déclarez pas de gagnant |
| Résultats différents d'une exécution à l'autre (mode réel) | les modèles ne sont pas parfaitement stables | Relancez 2 fois et mentionnez la variation dans la fiche |
| Quota Groq dépassé | trop de requêtes par minute | Attendez une minute ; le code réessaie une fois tout seul |

## Ce que je dois savoir expliquer

1. **Pourquoi ne change-t-on qu'une seule variable à la fois ?**
   Sinon on ne sait pas laquelle explique l'écart observé.
2. **Pourquoi exprimer l'écart en nombre de demandes ?**
   Avec 20 demandes, un écart de 1 ou 2 peut être dû au hasard ; dire « 12 demandes sur 20 » est plus honnête que « +60 % ».

*Terminez par `FICHE_PROJET.md` et `SOUTENANCE.md`.*
