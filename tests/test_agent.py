"""ÉTAPE 4 : la boucle de l'agent (historique, tool_call_id, max_tours, garde-fou)."""
from types import SimpleNamespace

from app import outils
from app.agent import executer_agent
from app.mock_llm import faire_message
from app.providers import MockProvider
from app.schemas import Statut
from app.service import traiter_demande


class Scenario:
    """Fournisseur scripté : renvoie des messages préparés et garde ce qu'il a reçu."""
    name = "scenario"
    model = "scenario"

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.vus = []

    def appeler(self, messages, schemas):
        self.vus.append(list(messages))
        return self.reponses.pop(0)


class SansFin:
    """Fournisseur qui redemande toujours un outil : l'agent ne conclut jamais."""
    name = "sans-fin"
    model = "sans-fin"

    def appeler(self, messages, schemas):
        return faire_message("", [("lister_evenements", {})], numero=len(messages))


def test_boucle_simple_outil_puis_texte():
    f = Scenario([faire_message("", [("lister_evenements", {"sport": "basket"})]),
                  faire_message("Voilà.")])
    sortie = executer_agent("Quels tournois de basket ?", f)
    assert sortie["reponse"] == "Voilà." and sortie["tours"] == 2 and not sortie["abandon"]
    assert sortie["appels"][0]["outil"] == "lister_evenements"


def test_historique_demande_avant_resultat_et_tool_call_id():
    f = Scenario([faire_message("", [("lister_evenements", {})]), faire_message("ok")])
    executer_agent("Quels événements ?", f)
    messages = f.vus[1]                                   # ce que le modèle voit au 2e tour
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user", "assistant", "tool"]   # assistant AVANT tool
    assert messages[3]["tool_call_id"] == messages[2]["tool_calls"][0]["id"]


def test_arguments_json_invalides_traites_comme_vides():
    cassé = SimpleNamespace(content="", tool_calls=[SimpleNamespace(
        id="x1", function=SimpleNamespace(name="verifier_eligibilite", arguments="pas du json"))])
    f = Scenario([cassé, faire_message("fini")])
    sortie = executer_agent("Puis-je participer ?", f)
    assert sortie["appels"][0]["arguments"] == {}
    assert "erreur" in sortie["appels"][0]["resultat"]    # erreur lisible, pas de plantage


def test_max_tours_declenche_abandon():
    sortie = executer_agent("Quels événements ?", SansFin(), max_tours=3)
    assert sortie["abandon"] is True and sortie["tours"] == 3 and len(sortie["appels"]) == 3


def test_abandon_part_en_revue_sans_erreur_http():
    s = traiter_demande("Quels événements proposez-vous ?", SansFin(), max_tours=2)
    assert s["abandon"] and s["requires_review"] and s["statut"] == Statut.a_verifier


def test_garde_fou_bloque_une_inscription_non_demandee():
    # Le modèle essaie de créer une inscription alors que l'utilisateur pose juste une question.
    f = Scenario([faire_message("", [("creer_inscription",
                                      {"id_evenement": "E02", "nom": "Karim", "age": 17})]),
                  faire_message("ok")])
    sortie = executer_agent("Puis-je m'inscrire au basket ? J'ai 17 ans.", f)
    assert sortie["appels"][0]["resultat"].get("bloque") is True
    assert len(outils.INSCRIPTIONS) == 2                  # rien n'a été créé


def test_le_modele_ne_peut_pas_forcer_une_inscription():
    # Demande explicite, mais l'événement est complet : la règle du code gagne.
    f = Scenario([faire_message("", [("creer_inscription",
                                      {"id_evenement": "E04", "nom": "Yacine", "age": 30})]),
                  faire_message("ok")])
    sortie = executer_agent("Inscris-moi à E04, j'ai 30 ans, je m'appelle Yacine.", f)
    assert sortie["appels"][0]["resultat"]["inscrit"] is False
    assert len(outils.INSCRIPTIONS) == 2


def test_une_question_ne_cree_aucune_inscription_avec_le_mock():
    s = traiter_demande("Puis-je m'inscrire au volley ? J'ai 19 ans.", MockProvider())
    assert all(a["outil"] != "creer_inscription" for a in s["actions"])
    assert len(outils.INSCRIPTIONS) == 2


def test_le_mock_enchaine_trois_outils():
    s = traiter_demande("Je veux m'inscrire au volley. J'ai 19 ans, je m'appelle Nour.", MockProvider())
    assert [a["outil"] for a in s["actions"]] == ["lister_evenements", "verifier_eligibilite", "creer_inscription"]
    assert s["statut"] == Statut.inscrit and s["tours"] == 4
