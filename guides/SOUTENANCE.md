# Plan de soutenance — 10 minutes

Préparez deux terminaux : un pour `uvicorn app.main:app`, un pour les commandes. Testez tout la veille.

| Minutes | Quoi | Commande ou support |
|---|---|---|
| 0:00 – 1:00 | **Présenter le projet** : l'idée, les 3 outils, le principe « le code décide, pas le modèle » | schéma de la boucle (étape 4) |
| 1:00 – 3:00 | **Cas réussi** : inscription complète | `python mesures/essayer.py "Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim."` ou `/docs` |
| 3:00 – 5:00 | **Cas refusé ou envoyé en revue** | voir ci-dessous |
| 5:00 – 6:30 | **Erreur gérée (503)** | `SIMULER_PANNE=1` dans `.env`, relancer, envoyer une demande |
| 6:30 – 9:00 | **Mesures et seuil** | `python mesures/comparer.py`, `python mesures/seuil.py`, la fiche d'une page |
| 9:00 – 10:00 | **Limites et conclusion** | ce que le mock ne prouve pas |

## Les démonstrations

1. **Cas réussi** : « Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim. » → `statut=inscrit`, numéro INS-003.
2. **Cas refusé par une règle** : « Inscris-moi à la course E04, j'ai 30 ans, je m'appelle Yacine. » → refus « complet », c'est la **règle** qui décide.
3. **Cas envoyé en revue** : « Inscris-moi à un tournoi, j'ai 20 ans. » → `requires_review=True`, confiance 0,2.
4. **Garde-fou** : « Puis-je m'inscrire au volley ? J'ai 19 ans. » → vérification, **aucune inscription**.
5. **Refus explicite** : « Inscris mon ami Karim au basket, il a 17 ans. » → refus, sans appel au modèle.
6. **Erreur gérée** : fournisseur en panne → **503** avec message générique ; montrez que le détail n'apparaît pas dans la réponse.

## Questions probables, et réponses courtes

- **Pourquoi 422 et 503 ?** 422 : requête invalide, faute du client. 503 : service indisponible, le client peut réessayer.
- **À quoi sert `tool_call_id` ?** À relier chaque résultat d'outil à la demande du modèle qui l'a provoqué.
- **À quoi sert `max_tours` ?** Éviter une boucle sans fin qui vide le quota ; au-delà, `abandon=True` et revue humaine.
- **Pourquoi les règles sont-elles dans le code ?** Une consigne peut être ignorée par le modèle, une règle Python s'applique toujours.
- **Comment avez-vous choisi le seuil ?** Avec `seuil.py` : on essaie tous les seuils et on compte faux négatifs et faux positifs ; le seuil retenu se place entre les deux groupes de confiances (voir la fiche).
- **Pourquoi seulement 20 demandes ?** C'est le minimum du sujet ; c'est pour cela qu'on n'affirme une différence qu'à partir de 3 demandes d'écart.
- **Le mock prouve-t-il que l'agent est bon ?** Non : il prouve que le code et les métriques fonctionnent. Les chiffres du mock ne disent rien sur un vrai modèle.
- **Qu'est-ce qu'un faux négatif ici ?** Une demande à revoir qui ne l'est pas : le plus grave, car personne ne la regarde.

## Check-list de la veille

- [ ] `pytest -q` vert.
- [ ] `.env` présent, **aucune vraie clé** dans le dépôt Git.
- [ ] Les deux variantes d'évaluation lancées, résultats dans `resultats/`.
- [ ] `FICHE_PROJET.md` remplie avec vos chiffres, fournisseur indiqué.
- [ ] Vous savez expliquer chaque fichier de `app/` en une phrase.
