"""Les outils de l'agent.

Un outil = (1) une fonction Python ordinaire + (2) une DESCRIPTION en JSON Schema.
Le modèle ne lit jamais notre code : il lit la description. Si elle est vague,
il se trompera d'outil.
"""
import json

from pydantic import ValidationError

from app.config import DATA_DIR
from app.regles import verifier_regles
from app.schemas import ArgsEligibilite, ArgsInscription, ArgsListe, Sport

# ---------- Les données (en mémoire) ----------
EVENEMENTS = []
INSCRIPTIONS = []


def recharger_donnees():
    """Remet les données dans leur état de départ (utile pour les tests et les mesures)."""
    EVENEMENTS.clear()
    INSCRIPTIONS.clear()
    EVENEMENTS.extend(json.loads((DATA_DIR / "evenements.json").read_text(encoding="utf-8")))
    INSCRIPTIONS.extend(json.loads((DATA_DIR / "inscriptions.json").read_text(encoding="utf-8")))


recharger_donnees()


def trouver_evenement(id_evenement):
    for evenement in EVENEMENTS:
        if evenement["id"] == id_evenement:
            return evenement
    return None


# ---------- Les 3 fonctions ----------

def lister_evenements(sport=None):
    """Lecture seule : aucun effet."""
    trouves = [e for e in EVENEMENTS if sport is None or e["sport"] == sport]
    return {"nombre": len(trouves), "evenements": trouves}


def verifier_eligibilite(id_evenement, age):
    """Lecture seule : dit si l'âge, les places et la date permettent de s'inscrire."""
    evenement = trouver_evenement(id_evenement)
    if evenement is None:
        return {"erreur": f"événement inconnu : {id_evenement}"}
    ok, raison = verifier_regles(evenement, age)
    return {"id_evenement": id_evenement, "titre": evenement["titre"],
            "eligible": ok, "raison": raison, "prix": evenement["prix"]}


def creer_inscription(id_evenement, nom, age):
    """SEULE action avec effet : elle modifie les données."""
    evenement = trouver_evenement(id_evenement)
    if evenement is None:
        return {"inscrit": False, "erreur": f"événement inconnu : {id_evenement}"}
    ok, raison = verifier_regles(evenement, age, nom, INSCRIPTIONS)
    if not ok:
        return {"inscrit": False, "raison": raison}
    evenement["places"] -= 1
    numero = f"INS-{len(INSCRIPTIONS) + 1:03d}"
    INSCRIPTIONS.append({"numero": numero, "id_evenement": id_evenement, "nom": nom, "age": age})
    return {"inscrit": True, "numero": numero, "id_evenement": id_evenement,
            "titre": evenement["titre"], "date": evenement["date"], "nom": nom,
            "prix": evenement["prix"]}


# ---------- Les descriptions JSON Schema ----------

def schema(nom, description, parametres, requis):
    return {"type": "function", "function": {
        "name": nom,
        "description": description,
        "parameters": {"type": "object", "properties": parametres, "required": requis}}}


SPORT = {"type": "string", "enum": [s.value for s in Sport], "description": "Le sport voulu"}
ID_EVENEMENT = {"type": "string", "pattern": "^E[0-9]{2}$",
                "description": "Identifiant de l'événement : E suivi de 2 chiffres, ex. E02"}
AGE = {"type": "integer", "minimum": 5, "maximum": 99, "description": "Âge en années"}
NOM = {"type": "string", "minLength": 2, "maxLength": 50, "description": "Prénom ou nom de l'inscrit"}

SCHEMAS = [
    schema("lister_evenements",
           "Liste les événements sportifs proposés (football, basket, natation, course, "
           "tennis, volley) avec date, lieu, âge, places et prix. À utiliser quand "
           "l'utilisateur cherche un sport, un tournoi, une date ou demande ce qui est proposé.",
           {"sport": SPORT}, []),
    schema("verifier_eligibilite",
           "Vérifie si une personne peut s'inscrire à un événement : âge dans la tranche, "
           "places restantes, date limite. À utiliser dès que l'utilisateur donne son âge et "
           "demande s'il peut participer, et toujours avant de créer une inscription.",
           {"id_evenement": ID_EVENEMENT, "age": AGE}, ["id_evenement", "age"]),
    schema("creer_inscription",
           "Crée une inscription (seule action qui modifie quelque chose). À utiliser "
           "UNIQUEMENT si l'utilisateur demande explicitement de l'inscrire (« inscris-moi », "
           "« je veux m'inscrire ») et a donné son nom, son âge et l'événement. Jamais pour "
           "une simple question.",
           {"id_evenement": ID_EVENEMENT, "nom": NOM, "age": AGE},
           ["id_evenement", "nom", "age"]),
]


def vaguer(schemas):
    """Variante VAGUE : la description devient le simple nom de l'outil (étape 5)."""
    vagues = []
    for s in schemas:
        f = s["function"]
        parametres = {cle: {k: v for k, v in p.items() if k != "description"}
                      for cle, p in f["parameters"]["properties"].items()}
        vagues.append(schema(f["name"], f["name"].replace("_", " "),
                             parametres, f["parameters"]["required"]))
    return vagues


SCHEMAS_VAGUES = vaguer(SCHEMAS)

# ---------- Exécuter un outil par son nom, sans jamais planter ----------

OUTILS = {
    "lister_evenements": (ArgsListe, lister_evenements),
    "verifier_eligibilite": (ArgsEligibilite, verifier_eligibilite),
    "creer_inscription": (ArgsInscription, creer_inscription),
}


def executer_outil(nom, arguments):
    """Toute erreur devient un résultat {"erreur": ...} que le modèle peut lire."""
    if nom not in OUTILS:
        return {"erreur": f"outil inconnu : {nom}"}
    modele_args, fonction = OUTILS[nom]
    try:
        args = modele_args(**arguments)
    except (ValidationError, TypeError) as exc:
        if isinstance(exc, ValidationError):
            details = "; ".join(f"{'.'.join(map(str, e['loc']))} : {e['msg']}" for e in exc.errors())
        else:
            details = "arguments mal formés"
        return {"erreur": f"arguments invalides ({details})"}
    try:
        return fonction(**args.model_dump(mode="json"))
    except Exception:
        return {"erreur": "erreur interne de l'outil"}
