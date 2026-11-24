"""Évalue l'assistant sur les 20 demandes de data/taches.csv.

Usage (depuis le dossier inscription-sport/) :
    python mesures/evaluer_agent.py                 # descriptions précises
    python mesures/evaluer_agent.py vagues          # descriptions vagues (une seule variable change)
    python mesures/evaluer_agent.py precises openai/gpt-oss-20b    # autre modèle (mode réel)
"""
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # pour trouver le dossier app/

from app import outils
from app.config import DATA_DIR, MODE, RESULTATS_DIR
from app.providers import get_provider
from app.service import traiter_demande
from metriques import (bons_outils, erreurs_de_revue, inscriptions_non_demandees,
                       reponse_juste, separer, tentatives_bloquees)


def charger_taches():
    with open(DATA_DIR / "taches.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluer(variante="precises", modele=None):
    fournisseur = get_provider(MODE, modele)
    schemas = outils.SCHEMAS_VAGUES if variante == "vagues" else outils.SCHEMAS
    etiquette = f"{fournisseur.model.replace('/', '-')}__{variante}"
    if MODE == "real" and fournisseur.name == "mock":
        print("ATTENTION : mode réel demandé mais clé absente -> repli sur le mock")

    taches, debut = [], time.time()
    for t in charger_taches():
        outils.recharger_donnees()                  # chaque demande repart des mêmes données
        sortie = traiter_demande(t["demande"], fournisseur, schemas)
        actions = sortie["actions"]
        appeles = [a["outil"] for a in actions]
        demande = t["demande_inscription"] == "1"
        bons = bons_outils(separer(t["outils_attendus"]), appeles, t["consultation_toleree"] == "1")
        juste = reponse_juste(sortie["reponse"], t["faits_attendus"])
        taches.append({
            "id": t["id"], "type": t["type"], "demande": t["demande"],
            "appeles": appeles, "attendus": separer(t["outils_attendus"]),
            "reponse": sortie["reponse"], "statut": sortie["statut"].value,
            "confiance": sortie["confiance"], "requires_review": sortie["requires_review"],
            "revue_attendue": t["revue_attendue"] == "1",
            "bons_outils": bons, "juste": juste, "reussie": bons and juste,
            "non_demandees": inscriptions_non_demandees(actions, demande),
            "bloquees": tentatives_bloquees(actions, demande),
            "abandon": sortie["abandon"], "tours": sortie["tours"],
        })

    n = len(taches)
    fp, fn = erreurs_de_revue([x["revue_attendue"] for x in taches],
                              [x["requires_review"] for x in taches])
    resume = {
        "etiquette": etiquette, "provider": fournisseur.name, "modele": fournisseur.model,
        "variante": variante, "nb_taches": n,
        "reussies": sum(x["reussie"] for x in taches),
        "bons_outils": sum(x["bons_outils"] for x in taches),
        "reponses_justes": sum(x["juste"] for x in taches),
        "appels_par_demande": round(sum(len(x["appeles"]) for x in taches) / n, 2),
        "inscriptions_non_demandees": sum(x["non_demandees"] for x in taches),
        "tentatives_bloquees": sum(x["bloquees"] for x in taches),
        "abandons": sum(x["abandon"] for x in taches),
        "revue_faux_positifs": fp, "revue_faux_negatifs": fn,
        "duree_s": round(time.time() - debut, 1),
    }
    RESULTATS_DIR.mkdir(exist_ok=True)
    (RESULTATS_DIR / f"{etiquette}.json").write_text(
        json.dumps({"resume": resume, "taches": taches}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return resume, taches


def afficher(resume, taches):
    n = resume["nb_taches"]
    print(f"=== {resume['etiquette']} ===")
    print(f"taches reussies            : {resume['reussies'] / n:.3f}  ({resume['reussies']}/{n})")
    print(f"bons outils                : {resume['bons_outils'] / n:.3f}")
    print(f"reponses justes            : {resume['reponses_justes'] / n:.3f}")
    print(f"appels par demande         : {resume['appels_par_demande']}")
    print(f"inscriptions non demandees : {resume['inscriptions_non_demandees']}"
          f"   (tentatives bloquees : {resume['tentatives_bloquees']})")
    print(f"abandons                   : {resume['abandons']}")
    print(f"revue : faux positifs {resume['revue_faux_positifs']}, "
          f"faux negatifs {resume['revue_faux_negatifs']}")
    print(f"duree                      : {resume['duree_s']} s")
    rates = [x for x in taches if not x["reussie"]]
    print("Demandes ratees" + (" : aucune" if not rates else ""))
    for x in rates:
        print(f"  {x['id']} attendu {x['attendus']} appele {x['appeles']}")
    print(f"Resultats enregistres dans resultats/{resume['etiquette']}.json")


if __name__ == "__main__":
    variante = sys.argv[1] if len(sys.argv) > 1 else "precises"
    modele = sys.argv[2] if len(sys.argv) > 2 else None
    afficher(*evaluer(variante, modele))
