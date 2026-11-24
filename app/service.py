"""Le service : assemble l'analyse, les refus du code, l'agent et la décision finale."""
from app.agent import executer_agent
from app.analyse import MESSAGES_REFUS, analyser_message
from app.config import MAX_TOURS, REVIEW_THRESHOLD
from app.outils import SCHEMAS
from app.schemas import Intention, Statut


def traiter_demande(message, fournisseur, schemas=SCHEMAS, max_tours=MAX_TOURS):
    analyse = analyser_message(message)

    # 1. Refus décidés par le CODE (hors sujet, inscrire un tiers, données d'autrui)
    if analyse["refus"]:
        return {"intention": analyse["intention"], "statut": Statut.refuse,
                "confiance": analyse["confiance"], "reponse": MESSAGES_REFUS[analyse["refus"]],
                "actions": [], "requires_review": False, "tours": 0, "abandon": False}

    # 2. L'agent travaille avec ses outils
    sortie = executer_agent(message, fournisseur, schemas, max_tours)
    actions = sortie["appels"]

    # 3. Le statut est décidé par le code, d'après ce qui s'est RÉELLEMENT passé
    inscrit = any(a["outil"] == "creer_inscription" and a["resultat"].get("inscrit")
                  for a in actions)
    if sortie["abandon"]:
        statut = Statut.a_verifier
    elif inscrit:
        statut = Statut.inscrit
    elif analyse["intention"] == Intention.inscription:
        incertain = analyse["manques"] or analyse["confiance"] < REVIEW_THRESHOLD
        statut = Statut.a_verifier if incertain else Statut.refuse
    else:
        statut = Statut.information

    # 4. Revue humaine : confiance sous le seuil, ou agent qui a abandonné
    requires_review = sortie["abandon"] or analyse["confiance"] < REVIEW_THRESHOLD

    reponse = sortie["reponse"]
    if sortie["abandon"]:
        reponse = "Je n'ai pas réussi à traiter cette demande : elle est transmise à un humain."

    return {"intention": analyse["intention"], "statut": statut,
            "confiance": analyse["confiance"], "reponse": reponse, "actions": actions,
            "requires_review": requires_review, "tours": sortie["tours"],
            "abandon": sortie["abandon"]}
