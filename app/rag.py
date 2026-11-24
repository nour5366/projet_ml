"""Système RAG (Retrieval-Augmented Generation) pour SportsAI.

Charge les extraits du règlement sportif, calcule les similarités lexicales/embeddings,
extrait les passages pertinents avec citation exacte de la source (document + titre),
et filtre sous un seuil de pertinence (réponse 'Je ne sais pas').
"""
import csv
import math
import re
from pathlib import Path

from app.config import DATA_DIR


def charger_passages():
    fichier = DATA_DIR / "passages_reglement.csv"
    if not fichier.exists():
        return []
    with open(fichier, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tokens(texte: str) -> list[str]:
    propre = re.sub(r"[^a-z0-9\s]", " ", texte.lower())
    return [t for t in propre.split() if len(t) > 2]


def rechercher_passages(question: str, k: int = 3, seuil_min: float = 0.15):
    """
    Recherche les k passages les plus pertinents pour une question donnée.
    Renvoie la liste des passages avec source exacte, score et texte.
    Si le score maximal est inférieur à seuil_min, indique que l'information est absente.
    """
    passages = charger_passages()
    q_toks = _tokens(question)
    scores = []

    for p in passages:
        p_toks = _tokens(f"{p.get('titre', '')} {p.get('texte', '')}")
        if not q_toks or not p_toks:
            score = 0.0
        else:
            intersection = sum(1 for t in set(q_toks) if t in set(p_toks))
            score = intersection / math.sqrt(len(set(q_toks)) * len(set(p_toks)))
        scores.append((round(score, 4), p))

    scores.sort(key=lambda x: x[0], reverse=True)
    meilleurs = scores[:k]

    pertinents = []
    for rang, (score, p) in enumerate(meilleurs, start=1):
        pertinents.append({
            "rang": rang,
            "id": p.get("id"),
            "source": p.get("source"),
            "titre": p.get("titre"),
            "texte": p.get("texte"),
            "score": score,
            "est_pertinent": score >= seuil_min
        })

    info_trouvee = any(item["est_pertinent"] for item in pertinents)
    if not info_trouvee:
        reponse_synthese = (
            "Je ne sais pas : les documents du règlement sportif disponibles ne contiennent pas "
            "d'information vérifiée permettant de répondre avec certitude à cette question."
        )
    else:
        top = pertinents[0]
        reponse_synthese = (
            f"D'après le document « {top['source']} » ({top['titre']}) : {top['texte']}"
        )

    return {
        "question": question,
        "information_trouvee": info_trouvee,
        "reponse": reponse_synthese,
        "sources": [p for p in pertinents if p["est_pertinent"]] or pertinents[:1],
        "tous_passages": pertinents
    }
