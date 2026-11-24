import csv
import json
from pathlib import Path

RESULTATS_DIR = Path(__file__).resolve().parent.parent / "resultats"
data = json.loads((RESULTATS_DIR / "mock-regles__precises.json").read_text(encoding="utf-8"))

taches = data["taches"]
csv_path = RESULTATS_DIR / "evaluation_20_cas_individuels.csv"

champs = [
    "id", "type", "demande", "appeles", "attendus", "statut", "confiance",
    "requires_review", "revue_attendue", "bons_outils", "juste", "reussie",
    "non_demandees", "bloquees", "tours"
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=champs)
    writer.writeheader()
    for t in taches:
        row = {
            "id": t["id"],
            "type": t["type"],
            "demande": t["demande"],
            "appeles": "|".join(t["appeles"]),
            "attendus": "|".join(t["attendus"]),
            "statut": t["statut"],
            "confiance": t["confiance"],
            "requires_review": t["requires_review"],
            "revue_attendue": t["revue_attendue"],
            "bons_outils": t["bons_outils"],
            "juste": t["juste"],
            "reussie": t["reussie"],
            "non_demandees": t["non_demandees"],
            "bloquees": t["bloquees"],
            "tours": t["tours"]
        }
        writer.writerow(row)

print(f"CSV généré : {csv_path} ({len(taches)} cas enregistrés)")
