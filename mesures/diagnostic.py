"""Diagnostic : pour chaque demande, qui a échoué ? (outils ou rédaction)

                    réponse juste      réponse fausse
   bons outils      ok                 REDACTION   (résultat mal lu)
   mauvais outils   detour             OUTILS      (mauvais choix d'outil)

Usage : python mesures/diagnostic.py <etiquette>      (aucun appel réseau)
        ex. python mesures/diagnostic.py mock-regles__precises
"""
import json
import sys
from pathlib import Path

RESULTATS_DIR = Path(__file__).resolve().parent.parent / "resultats"


def diagnostic(outils_ok, justes):
    """Reçoit deux listes de True/False de même longueur ; renvoie les POSITIONS de chaque case."""
    cases = {"ok": [], "redaction": [], "detour": [], "outils": []}
    for i, (bons, juste) in enumerate(zip(outils_ok, justes)):
        if bons and juste:
            cases["ok"].append(i)
        elif bons and not juste:
            cases["redaction"].append(i)
        elif not bons and juste:
            cases["detour"].append(i)
        else:
            cases["outils"].append(i)
    return cases


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python mesures/diagnostic.py <etiquette>")
        sys.exit(1)
    donnees = json.loads((RESULTATS_DIR / f"{sys.argv[1]}.json").read_text(encoding="utf-8"))
    taches = donnees["taches"]
    cases = diagnostic([t["bons_outils"] for t in taches], [t["juste"] for t in taches])
    print(f"=== diagnostic : {sys.argv[1]} ({len(taches)} demandes) ===")
    for nom, positions in cases.items():
        ids = " ".join(taches[i]["id"] for i in positions)
        print(f"{nom:<10}{len(positions):>3}   {ids}")
