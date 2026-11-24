"""Un faux modèle qui fonctionne avec des règles (hors ligne, toujours la même réponse).

ATTENTION : ce n'est PAS un modèle. C'est un simulateur qui produit le même TYPE de
message qu'un vrai modèle avec appel d'outils. Il sert à tester la boucle de l'agent.

Pour simuler l'effet des descriptions d'outils, il n'appelle un outil que s'il
"comprend" l'outil : au moins un mot de la demande se retrouve dans le nom ou la
description de l'outil. Ce n'est qu'une SIMULATION : refaites la mesure avec un vrai
modèle avant de conclure quoi que ce soit sur les vrais modèles.
"""
import json
from types import SimpleNamespace

from app.analyse import MESSAGES_REFUS, analyser_message, normaliser
from app.schemas import Intention

LIBELLES_MANQUES = {
    "evenement": "l'événement ou le sport",
    "age": "votre âge (entre 5 et 99 ans)",
    "nom": "votre nom",
}


# ---------- Fabriquer un message au même format qu'un vrai modèle ----------

def faire_message(contenu, appels=(), numero=0):
    tool_calls = [
        SimpleNamespace(id=f"mock_{numero}_{i}",
                        function=SimpleNamespace(name=nom, arguments=json.dumps(arguments)))
        for i, (nom, arguments) in enumerate(appels)
    ]
    return SimpleNamespace(content=contenu, tool_calls=tool_calls)


# ---------- Relire l'historique de la conversation ----------

def lire_historique(messages):
    """Renvoie la liste [{"outil", "arguments", "resultat"}, ...] des outils déjà appelés."""
    demandes = {}
    historique = []
    for m in messages:
        if m["role"] == "assistant":
            for appel in m.get("tool_calls", []):
                demandes[appel["id"]] = (appel["function"]["name"],
                                         json.loads(appel["function"]["arguments"]))
        elif m["role"] == "tool":
            nom, arguments = demandes[m["tool_call_id"]]
            historique.append({"outil": nom, "arguments": arguments,
                               "resultat": json.loads(m["content"])})
    return historique


def dernier_resultat(historique, outil):
    for h in reversed(historique):
        if h["outil"] == outil:
            return h["resultat"]
    return None


# ---------- "Comprendre" un outil ----------

def racines(texte):
    """Les 5 premières lettres de chaque mot : 'inscrire' et 'inscris' -> 'inscr'."""
    return {mot[:5] for mot in normaliser(texte).split() if len(mot) >= 4}


def outil_compris(schemas, nom, demande):
    for s in schemas:
        if s["function"]["name"] == nom:
            texte = nom.replace("_", " ") + " " + s["function"]["description"]
            return bool(racines(texte) & racines(demande))
    return False      # l'outil n'est pas dans la liste fournie


# ---------- Décider du prochain outil ----------

def evenement_unique(historique):
    liste = dernier_resultat(historique, "lister_evenements")
    if liste and len(liste.get("evenements", [])) == 1:
        return liste["evenements"][0]["id"]
    return None


def choisir_outil(analyse, historique, schemas, demande):
    """Renvoie (nom_outil, arguments) ou None quand il faut répondre en texte."""
    deja = [h["outil"] for h in historique]

    def peut(nom):
        return nom not in deja and outil_compris(schemas, nom, demande)

    if analyse["intention"] == Intention.hors_sujet:
        return None

    id_ev = analyse["id_evenement"] or evenement_unique(historique)
    sport, age = analyse["sport"], analyse["age"]

    # 1. Trouver l'événement
    if id_ev is None:
        if analyse["nb_sports"] > 1:
            return None                                  # ambigu : on demande de préciser
        veut_liste = sport is not None or analyse["intention"] == Intention.information
        if veut_liste and peut("lister_evenements"):
            return "lister_evenements", ({"sport": sport} if sport else {})
        return None

    # 2. Vérifier l'éligibilité
    if age is not None and peut("verifier_eligibilite"):
        return "verifier_eligibilite", {"id_evenement": id_ev, "age": age}

    # 3. Créer l'inscription (seulement si demandée, complète, et éligible)
    if analyse["intention"] == Intention.inscription and peut("creer_inscription"):
        verif = dernier_resultat(historique, "verifier_eligibilite")
        eligible = verif is None or verif.get("eligible") is True
        if analyse["nom"] and age is not None and eligible:
            return "creer_inscription", {"id_evenement": id_ev, "nom": analyse["nom"], "age": age}
    return None


# ---------- Rédiger la réponse en texte ----------

def date_fr(iso):
    annee, mois, jour = iso.split("-")
    return f"{jour}/{mois}/{annee}"


def prix_txt(prix):
    return "gratuit" if prix == 0 else f"{prix} euros"


def ligne_evenement(e):
    places = "complet" if e["places"] <= 0 else f"{e['places']} places"
    return (f"- {e['id']} : {e['titre']} le {date_fr(e['date'])} à {e['lieu']} "
            f"({e['age_min']}-{e['age_max']} ans, {places}, {prix_txt(e['prix'])})")


def phrase_manques(analyse):
    return ", ".join(LIBELLES_MANQUES[m] for m in analyse["manques"])


def rediger_reponse(analyse, historique):
    if analyse["intention"] == Intention.hors_sujet:
        return MESSAGES_REFUS["hors_sujet"]

    creation = dernier_resultat(historique, "creer_inscription")
    verif = dernier_resultat(historique, "verifier_eligibilite")
    liste = dernier_resultat(historique, "lister_evenements")

    if creation:
        if creation.get("inscrit"):
            return (f"Inscription confirmée pour {creation['nom']} : {creation['titre']} "
                    f"le {date_fr(creation['date'])}. Prix : {prix_txt(creation['prix'])}. "
                    f"Numéro : {creation['numero']}.")
        return "Inscription refusée : " + creation.get("raison", creation.get("erreur", "erreur"))

    if verif:
        if "erreur" in verif:
            return "Je n'ai pas pu vérifier l'éligibilité : " + verif["erreur"]
        if not verif["eligible"]:
            return "Non : " + verif["raison"]
        texte = (f"Vous pouvez vous inscrire à {verif['id_evenement']} "
                 f"({verif['titre']}) : prix {prix_txt(verif['prix'])}.")
        if analyse["intention"] == Intention.inscription and analyse["manques"]:
            return texte + f" Il me manque : {phrase_manques(analyse)}. Précisez-le pour confirmer."
        return texte + " Dites « inscris-moi » pour confirmer."

    if analyse["intention"] == Intention.inscription:
        if analyse["nb_sports"] > 1:
            return (f"Plusieurs sports sont cités ({', '.join(analyse['sports'])}) : "
                    "précisez lequel.")
        if analyse["manques"]:
            return f"Pour vous inscrire, il me manque : {phrase_manques(analyse)}. Précisez-le."
        return "Je n'ai pas pu traiter cette demande."

    if liste:
        if liste["nombre"] == 0:
            return "Aucun événement ne correspond à votre recherche."
        return "Voici les événements :\n" + "\n".join(ligne_evenement(e) for e in liste["evenements"])

    return "Je ne peux pas répondre sans consulter la liste des événements."


# ---------- Le point d'entrée appelé par la boucle de l'agent ----------

def repondre(messages, schemas):
    demande = messages[1]["content"]            # messages[0] = consigne, messages[1] = utilisateur
    analyse = analyser_message(demande)
    historique = lire_historique(messages)
    choix = choisir_outil(analyse, historique, schemas, demande)
    if choix is None:
        return faire_message(rediger_reponse(analyse, historique))
    nom, arguments = choix
    return faire_message("", [(nom, arguments)], numero=len(messages))
