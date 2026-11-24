# Fiche d'une page — Projet de fin de module

**Nom, prénom :** ______________________  **Groupe :** ____________  **Date :** ____________

## 1. Thème

Assistant d'inscription à des événements sportifs : l'utilisateur écrit en langage naturel, un agent
utilise 3 outils (`lister_evenements`, `verifier_eligibilite`, `creer_inscription`), le code applique les
règles métier et n'inscrit que sur demande explicite.

Fournisseur et modèle utilisés pour les mesures ci-dessous : ______________________
(mock / Groq `qwen/qwen3.8-27b` / autre). **Indiquez-le : un chiffre du mock ne vaut pas un chiffre d'un vrai modèle.**

## 2. Mes mesures (20 demandes, commande : `python mesures/evaluer_agent.py`)

À remplir avec VOS résultats, à partir des fichiers de `resultats/`.

| Mesure | Descriptions précises | Descriptions vagues | Écart (en demandes) |
|---|---|---|---|
| Tâches réussies | ___ / 20 | ___ / 20 | ___ |
| Bons outils | ___ / 20 | ___ / 20 | ___ |
| Réponses justes | ___ / 20 | ___ / 20 | ___ |
| Appels par demande | ___ | ___ | — |
| Inscriptions non demandées | ___ | ___ | — |
| Abandons | ___ | ___ | — |

1 demande sur 20 = 5 points. Différence retenue seulement à partir de 3 demandes d'écart.

**Variable changée (une seule) :** ______________________  **Conclusion :** ______________________

**Diagnostic des échecs** (`python mesures/diagnostic.py <étiquette>`) :
ok ___ · rédaction ___ · détour ___ · outils ___ → cause principale : ______________________

**Latence** (`python mesures/latence.py`, bonus) : minimum ___ ms · médiane ___ ms · maximum ___ ms

## 3. Seuil de revue humaine retenu

`REVIEW_THRESHOLD` = ______

Pourquoi (sortie de `python mesures/seuil.py`) :
- Plus haute confiance d'une demande à revoir : ______
- Plus basse confiance d'une demande à ne pas revoir : ______
- Faux négatifs à ce seuil : ___ · faux positifs : ___
- Justification (2 phrases) : ____________________________________________________________

## 4. Une limite de mon travail

Ce qui n'est pas couvert ou pas fiable (exemples : jeu de test de seulement 20 demandes, simulateur
au lieu d'un vrai modèle, une seule exécution) : ______________________________________________

---

*Aide-mémoire pour remplir la section 3 avec les données fournies (mock) : plus haute confiance à
revoir 0,55 ; plus basse confiance à ne pas revoir 0,65 ; seuil 0,60 ; 0 faux négatif, 0 faux positif.
Ces valeurs viennent du jeu de 20 demandes fourni : si vous le modifiez, relancez le script.*
