"""Les règles métier : c'est le CODE qui décide, jamais le modèle.

Un modèle peut se tromper ou être manipulé. Ces règles, elles, sont écrites
une fois et s'appliquent toujours.
"""
from datetime import date

from app.config import AUJOURDHUI


def verifier_regles(evenement, age, nom=None, inscriptions=()):
    """Renvoie (True, "...") si l'inscription est possible, sinon (False, raison)."""
    # Règle 1 : la date limite d'inscription ne doit pas être dépassée
    limite = date.fromisoformat(evenement["date_limite"])
    if limite < AUJOURDHUI:
        return False, f"la date limite d'inscription ({limite.strftime('%d/%m/%Y')}) est dépassée."

    # Règle 2 : il doit rester des places
    if evenement["places"] <= 0:
        return False, "l'événement est complet (plus aucune place)."

    # Règle 3 : l'âge doit être dans la tranche autorisée
    if not evenement["age_min"] <= age <= evenement["age_max"]:
        return False, (f"l'âge ({age} ans) est hors de la tranche "
                       f"{evenement['age_min']}-{evenement['age_max']} ans.")

    # Règle 4 : pas de doublon (même personne, même événement)
    if nom:
        for ins in inscriptions:
            if ins["id_evenement"] == evenement["id"] and ins["nom"].lower() == nom.lower():
                return False, f"{nom} est déjà inscrit(e) à cet événement."

    return True, "inscription possible."
