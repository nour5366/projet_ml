import csv
import math
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from app.rag import rechercher_passages

with open(BASE / "data/questions_rag.csv", encoding="utf-8") as f:
    questions = list(csv.DictReader(f))

repondables = [q for q in questions if q["repondable"] == "1"]
non_repondables = [q for q in questions if q["repondable"] == "0"]
total = len(repondables)

r1 = 0
r3 = 0
r5 = 0

print(f"=== Évaluation RAG sur 20 questions ({total} répondables, {len(non_repondables)} hors corpus) ===")
details = []
for q in repondables:
    attendu = q["passages_attendus"].strip()
    res5 = rechercher_passages(q["question"], k=5)["tous_passages"]
    recup_ids_5 = [item["id"] for item in res5]
    recup_ids_3 = recup_ids_5[:3]
    recup_ids_1 = recup_ids_5[:1]

    hit1 = attendu in recup_ids_1
    hit3 = attendu in recup_ids_3
    hit5 = attendu in recup_ids_5

    if hit1: r1 += 1
    if hit3: r3 += 1
    if hit5: r5 += 1

    status = "OK (Top-1)" if hit1 else ("OK (Top-3)" if hit3 else ("OK (Top-5)" if hit5 else "MISS"))
    details.append((q["id"], q["question"][:45] + "...", attendu, recup_ids_3, status))
    print(f"[{q['id']}] {status:<10} | attendu={attendu} | top3={recup_ids_3}")

print("\n=== Synthèse Recall@k ===")
print(f"Recall@1 : {r1}/{total} = {r1/total:.3f} ({r1/total*100:.1f}%)")
print(f"Recall@3 : {r3}/{total} = {r3/total:.3f} ({r3/total*100:.1f}%)")
print(f"Recall@5 : {r5}/{total} = {r5/total:.3f} ({r5/total*100:.1f}%)")

print("\n=== Questions hors corpus (Réponse attendue : non répondable / Je ne sais pas) ===")
for q in non_repondables:
    res = rechercher_passages(q["question"], k=1)
    best_score = res["tous_passages"][0]["score"] if res["tous_passages"] else 0.0
    info_trouvee = res["information_trouvee"]
    print(f"[{q['id']}] {q['question'][:50]}... | score max = {best_score:.4f} | info_trouvee = {info_trouvee}")

