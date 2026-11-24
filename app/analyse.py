"""Analyse du message par des règles simples (aucun modèle ici).

Ce module sert à trois choses :
  1. repérer l'intention (inscription, information, hors sujet),
  2. calculer un score de confiance -> décide du seuil de revue humaine,
  3. servir de garde-fou : le code vérifie lui-même ce que l'utilisateur a demandé.
"""
import re
import unicodedata

from app.schemas import Intention, Sport

MESSAGES_REFUS = {
    "hors_sujet": "Je ne peux répondre qu'aux questions sur les événements sportifs et les inscriptions.",
    "tiers": "Je ne peux inscrire que vous-même : chaque personne doit faire sa propre demande.",
    "donnees": "Je ne peux pas communiquer les données d'autres participants (confidentialité).",
}

MOTS_SPORTS = {
    "football": {"football", "foot"},
    "basket": {"basket", "basketball"},
    "natation": {"natation", "piscine", "nager"},
    "course": {"course", "courir", "marathon"},
    "tennis": {"tennis"},
    "volley": {"volley", "volleyball"},
}

# Mots qui montrent que le message parle bien de sport / d'inscription
MOTS_SPORTIFS = {"evenement", "evenements", "tournoi", "tournois", "match", "matchs", "sport",
                 "sports", "competition", "stage", "gala", "inscription", "inscrire", "inscris",
                 "inscri", "participer", "place", "places", "tarif", "reserver", "propose",
                 "proposes", "proposez"}

MOTS_DONNEES = ["coordonnees", "numero de telephone", "telephone de", "adresse de",
                "adresse mail", "email de", "mail de", "liste des inscrits",
                "qui est inscrit", "qui participe", "liste des participants", "donnees de"]

RE_TIERS = re.compile(
    r"\b(mon|ma|mes|son|sa|ses)\s+(petit |petite |meilleur |meilleure )?"
    r"(ami|amie|amis|pote|copain|copine|frere|soeur|fils|fille|cousin|cousine|"
    r"collegue|voisin|voisine|enfant|enfants)\b"
    r"|\bquelqu un d autre\b|\bpour lui\b|\bpour elle\b|\ba sa place\b")

RE_NOM = re.compile(
    r"(?i:je m['’ ]?appelle|mon nom est|mon prenom est|moi c['’ ]?est|nom ?:)\s*"
    r"([A-ZÀ-Ý][A-Za-zÀ-ÿ\-]{1,29})")

MARQUEURS_QUESTION = ["puis je", "est ce que", "comment", "savoir si", "conditions"]
RE_IMPERATIF = re.compile(r"\binscri(?:s|vez)?\b")          # inscris-moi, inscri moi, inscrivez-moi
RE_SOUHAIT = re.compile(r"\b(je veux|je voudrais|j aimerais|je souhaite)\b.*\b(inscrire|inscription|participer|reserver)\b")
RE_DEMANDE = re.compile(r"\b(peux tu|tu peux|pouvez vous|vous pouvez)\s+(m )?(inscrire|reserver)\b")
RE_RESERVE = re.compile(r"\b(reserve|reservez)\b")


def normaliser(texte):
    """minuscules, sans accents, sans ponctuation : 'Inscris-moi à E02 !' -> 'inscris moi a e02'."""
    texte = texte.lower().replace("’", "'")
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")   # retire les accents
    texte = re.sub(r"[^a-z0-9 ]", " ", texte)                              # ponctuation -> espace
    return " ".join(texte.split())


def demande_explicite(message):
    """True seulement si l'utilisateur DEMANDE de l'inscrire (pas s'il pose une question)."""
    t = normaliser(message)
    if RE_IMPERATIF.search(t):
        return True
    if any(m in t for m in MARQUEURS_QUESTION):
        return False
    return bool(RE_SOUHAIT.search(t) or RE_DEMANDE.search(t) or RE_RESERVE.search(t))


def trouver_sports(mots):
    return [sport for sport, synonymes in MOTS_SPORTS.items() if mots & synonymes]


def trouver_age(t):
    m = re.search(r"\b(\d{1,3})\s*ans\b", t) or re.search(r"\bage (?:de |est )?(\d{1,3})\b", t)
    if not m:
        return None
    age = int(m.group(1))
    return age if 5 <= age <= 99 else None     # un âge absurde compte comme "manquant"


def calculer_confiance(intention, id_ev, sports, age, nom):
    """Score entre 0 et 1. On retire des points pour chaque information manquante."""
    if intention != Intention.inscription:
        return 0.90
    confiance = 0.95
    if id_ev is None and len(sports) == 0:
        confiance -= 0.45          # on ne sait pas à quel événement
    if id_ev is None and len(sports) > 1:
        confiance -= 0.40          # plusieurs sports : ambigu
    if age is None:
        confiance -= 0.40
    if nom is None:
        confiance -= 0.30
    return round(max(confiance, 0.05), 2)


def analyser_message(message):
    t = normaliser(message)
    mots = set(t.split())

    sports = trouver_sports(mots)
    m_id = re.search(r"\be(\d{2})\b", t)
    id_ev = f"E{m_id.group(1)}" if m_id else None
    age = trouver_age(t)
    m_nom = RE_NOM.search(message.replace("’", "'"))
    nom = m_nom.group(1) if m_nom else None

    tiers = bool(RE_TIERS.search(t))
    donnees = any(m in t for m in MOTS_DONNEES)
    explicite = demande_explicite(message)
    sportif = bool(sports or id_ev or (mots & MOTS_SPORTIFS))

    # Refus décidés par le CODE, avant tout appel au modèle
    refus = None
    if donnees:
        refus = "donnees"
    elif not sportif:
        refus = "hors_sujet"
    elif explicite and tiers:
        refus = "tiers"

    if not sportif:
        intention = Intention.hors_sujet
    elif explicite:
        intention = Intention.inscription
    else:
        intention = Intention.information

    # Ce qu'il manque pour pouvoir s'inscrire
    manques = []
    if intention == Intention.inscription:
        if id_ev is None and len(sports) != 1:
            manques.append("evenement")
        if age is None:
            manques.append("age")
        if nom is None:
            manques.append("nom")

    return {
        "intention": intention,
        "sport": sports[0] if len(sports) == 1 else None,
        "nb_sports": len(sports),
        "sports": sports,
        "id_evenement": id_ev,
        "age": age,
        "nom": nom,
        "manques": manques,
        "refus": refus,
        "confiance": calculer_confiance(intention, id_ev, sports, age, nom),
    }
