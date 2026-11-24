# Grille d'auto-évaluation (barème du sujet : 16 points essentiels + 4 soutenance, bonus plafonnés à 20)

Cochez une case seulement si vous pouvez **le montrer** à l'écran.

## Les 6 points essentiels (16 points)

| # | Critère | Pts | Preuve à montrer | ✔ |
|---|---|---|---|---|
| 1 | **API derrière un contrat** indépendant du fournisseur ; mock et réel ; clé dans `.env` | 2 | `schemas.py` sans nom de fournisseur · `/health` · `.env.example` sans secret | ☐ |
| 2 | **Sortie contrainte** : énumérations, bornes, au moins une règle métier qui décide à la place du modèle | 2 | `Sport`, `Statut` · âge 5-99 · refus « complet » par `regles.py` | ☐ |
| 3 | **« Je ne sais pas »** : seuil de revue ou refus explicite, **justifié par les mesures** | 1 | `requires_review` · `seuil.py` · fiche d'une page | ☐ |
| 4 | **Agent avec outils** : au moins 3 outils JSON Schema, `max_tours`, aucune action non demandée | 4 | `outils.py` · `agent.py` · 0 inscription non demandée dans l'évaluation | ☐ |
| 5 | **Mesurer** : 20 demandes annotées minimum (cas difficiles et cas à refuser), métrique calculée par script | 3 | `taches.csv` · `evaluer_agent.py` · fichiers de `resultats/` | ☐ |
| 6 | **Comparer en changeant UNE variable** ; écart en nombre de demandes | 2 | `comparer.py` · tableau de la fiche | ☐ |

## Soutenance (4 points)

| Critère | ✔ |
|---|---|
| Un cas réussi | ☐ |
| Un cas refusé ou envoyé en revue | ☐ |
| Une erreur gérée (503) | ☐ |
| Explication des mesures et du seuil | ☐ |

## Bonus (4 points au maximum, seulement si les 6 points essentiels sont présents)

| Bonus | Pts | Fait dans ce projet ? | ✔ |
|---|---|---|---|
| Contenu multimédia (image ou audio) | +2 | Non fourni (atelier 3) | ☐ |
| RAG avec sources et Recall@k | +2 | Non fourni (atelier 4) | ☐ |
| Diagnostic des échecs | +1 | Oui : `mesures/diagnostic.py` | ☐ |
| Latence mesurée (min, médiane, max sur 20 appels) | +1 | Oui : `mesures/latence.py` — **refaites-la en mode réel** | ☐ |

## À rendre

- [ ] Dépôt Git avec le README pour installer et lancer.
- [ ] La sortie du script de mesure (`resultats/`).
- [ ] Une fiche d'une page : thème, mesures, seuil retenu et pourquoi (`FICHE_PROJET.md`).

*Auto-évaluation indicative : c'est l'enseignant qui note. Le projet fourni est un point de départ :
c'est à vous de l'exécuter, de comprendre chaque fichier et de produire vos propres mesures.*
