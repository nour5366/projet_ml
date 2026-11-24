"""Compare tous les fichiers de resultats/ : tableau, écart EN DEMANDES, demandes qui divergent.

Usage : python mesures/comparer.py
Règle : on ne déclare une différence qu'à partir de 3 demandes d'écart (1 demande sur 20 = 5 points).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # pour trouver le dossier app/

from app.config import RESULTATS_DIR

SEUIL_ECART = 3


def charger_resultats():
    fichiers = sorted(RESULTATS_DIR.glob("*.json"))
    return [json.loads(f.read_text(encoding="utf-8")) for f in fichiers]


def verdict(ecart):
    return "différence mesurable" if ecart >= SEUIL_ECART else "pas de différence mesurable"


def main():
    resultats = charger_resultats()
    if len(resultats) < 2:
        print("Il faut au moins 2 fichiers dans resultats/ : lancez evaluer_agent.py deux fois "
              "(precises puis vagues).")
        return
    resultats.sort(key=lambda r: r["resume"]["reussies"], reverse=True)
    meilleur = resultats[0]
    n = meilleur["resume"]["nb_taches"]

    print(f"{'agent':<34}{'réussite':>9}{'outils':>8}{'justes':>8}{'appels':>8}{'non dem.':>9}{'écart':>7}")
    for r in resultats:
        s = r["resume"]
        ecart = meilleur["resume"]["reussies"] - s["reussies"]
        print(f"{s['etiquette']:<34}{s['reussies']:>6}/{n:<2}{s['bons_outils']:>8}"
              f"{s['reponses_justes']:>8}{s['appels_par_demande']:>8}"
              f"{s['inscriptions_non_demandees']:>9}{ecart:>7}")

    print(f"\n(1 demande sur {n} = {100 / n:.1f} points ; différence retenue à partir de {SEUIL_ECART} demandes)")
    for r in resultats[1:]:
        ecart = meilleur["resume"]["reussies"] - r["resume"]["reussies"]
        print(f"- {meilleur['resume']['etiquette']} contre {r['resume']['etiquette']} : "
              f"{ecart} demande(s) d'écart -> {verdict(ecart)}")
        diverge = [(a["id"], a["demande"]) for a, b in zip(meilleur["taches"], r["taches"])
                   if a["reussie"] != b["reussie"]]
        for id_, demande in diverge[:8]:
            print(f"    {id_} {demande}")


if __name__ == "__main__":
    main()
