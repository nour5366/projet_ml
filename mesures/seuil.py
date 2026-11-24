"""Choisir le seuil de revue humaine PAR LES MESURES (aucun appel réseau).

Pour chaque seuil possible, on compte :
  - les faux négatifs : une demande qui AURAIT DÛ aller en revue mais n'y va pas (le plus grave),
  - les faux positifs : une demande envoyée en revue pour rien (coûte du temps humain).

Usage : python mesures/seuil.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # pour trouver le dossier app/

from app.analyse import analyser_message
from app.config import REVIEW_THRESHOLD
from evaluer_agent import charger_taches
from metriques import erreurs_de_revue


def main():
    taches = charger_taches()
    analyses = [analyser_message(t["demande"]) for t in taches]
    attendues = [t["revue_attendue"] == "1" for t in taches]

    print("Confiances observées :", sorted({a["confiance"] for a in analyses}))
    print(f"\n{'seuil':>6}{'faux positifs':>16}{'faux négatifs':>16}{'total':>8}")
    meilleurs = []
    meilleur_total = None
    for centieme in range(30, 100, 5):
        seuil = centieme / 100
        # le code a déjà refusé (refus) -> pas de revue ; sinon revue si confiance < seuil
        obtenues = [a["refus"] is None and a["confiance"] < seuil for a in analyses]
        fp, fn = erreurs_de_revue(attendues, obtenues)
        total = fp + fn
        print(f"{seuil:>6.2f}{fp:>16}{fn:>16}{total:>8}")
        if meilleur_total is None or total < meilleur_total:
            meilleur_total, meilleurs = total, [seuil]
        elif total == meilleur_total:
            meilleurs.append(seuil)

    print(f"\nSeuils testés qui font le moins d'erreurs ({meilleur_total}) : "
          f"de {min(meilleurs):.2f} à {max(meilleurs):.2f}")

    # Calcul exact : on sépare les demandes à revoir de celles qui ne le sont pas
    a_revoir = [a["confiance"] for a, att in zip(analyses, attendues) if att]
    pas_a_revoir = [a["confiance"] for a, att in zip(analyses, attendues)
                    if not att and a["refus"] is None]
    haut, bas = max(a_revoir), min(pas_a_revoir)
    print(f"Plus haute confiance d'une demande À REVOIR      : {haut:.2f}")
    print(f"Plus basse confiance d'une demande à NE PAS revoir : {bas:.2f}")
    if haut < bas:
        print(f"-> tout seuil dans ]{haut:.2f} ; {bas:.2f}] sépare parfaitement les deux groupes ;"
              f" le milieu est {(haut + bas) / 2:.2f}")
    else:
        print("-> les deux groupes se chevauchent : aucun seuil n'est parfait, il faut choisir"
              " quelle erreur on accepte (faux négatif = plus grave).")
    print(f"Seuil configuré (.env) : {REVIEW_THRESHOLD:.2f}")
    print("À justifier dans votre fiche d'une page avec ces chiffres.")


if __name__ == "__main__":
    main()
