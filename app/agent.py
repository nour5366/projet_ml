"""La boucle de l'agent : le modèle CHOISIT un outil, NOTRE code l'exécute.

   demande -> LLM -> "appelle l'outil X" -> notre code exécute X -> résultat renvoyé -> LLM ...
                                                                    ... jusqu'à une réponse en texte
"""
import json

from app.analyse import demande_explicite
from app.config import MAX_TOURS
from app.outils import SCHEMAS, executer_outil

CONSIGNE_AGENT = """Tu es l'assistant d'inscription aux événements sportifs.
Règles :
- Utilise les outils pour consulter les événements et vérifier les règles. N'invente jamais
  une date, un prix, une place ou un identifiant.
- Appelle creer_inscription UNIQUEMENT si l'utilisateur demande explicitement de l'inscrire
  et t'a donné son nom, son âge et l'événement. Pour une simple question, ne crée rien.
- Si une information manque (événement, âge, nom), demande-la sans appeler d'outil.
- Réponds en français, brièvement."""


def message_assistant(msg):
    """Remet la demande d'outil du modèle dans l'historique (obligatoire avant les résultats)."""
    return {"role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": a.id, "type": "function",
                            "function": {"name": a.function.name,
                                         "arguments": a.function.arguments}}
                           for a in msg.tool_calls]}


def executer_outil_garde(nom, arguments, message):
    """GARDE-FOU dans le code : pas d'inscription si l'utilisateur ne l'a pas demandée."""
    if nom == "creer_inscription" and not demande_explicite(message):
        return {"erreur": "inscription bloquée : l'utilisateur ne l'a pas demandée explicitement",
                "bloque": True}
    return executer_outil(nom, arguments)


def executer_agent(message, fournisseur, schemas=SCHEMAS, max_tours=MAX_TOURS):
    messages = [{"role": "system", "content": CONSIGNE_AGENT},
                {"role": "user", "content": message}]
    appels = []
    for tour in range(1, max_tours + 1):
        msg = fournisseur.appeler(messages, schemas)
        if not msg.tool_calls:                       # du texte : c'est fini
            return {"reponse": msg.content or "", "appels": appels,
                    "tours": tour, "abandon": False}
        messages.append(message_assistant(msg))      # AVANT les messages role=tool
        for appel in msg.tool_calls:
            try:
                arguments = json.loads(appel.function.arguments)
            except json.JSONDecodeError:
                arguments = {}                       # arguments cassés : on les traite comme vides
            if not isinstance(arguments, dict):
                arguments = {}
            resultat = executer_outil_garde(appel.function.name, arguments, message)
            appels.append({"outil": appel.function.name, "arguments": arguments,
                           "resultat": resultat})
            messages.append({"role": "tool", "tool_call_id": appel.id,   # le lien avec la demande
                             "content": json.dumps(resultat, ensure_ascii=False)})
    return {"reponse": "", "appels": appels, "tours": max_tours, "abandon": True}
