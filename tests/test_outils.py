"""ÉTAPE 3 : les outils, leurs descriptions JSON Schema et executer_outil()."""
import json

from app import outils


def test_lister_tous_les_evenements():
    assert outils.lister_evenements()["nombre"] == 6


def test_lister_par_sport():
    r = outils.lister_evenements("basket")
    assert r["nombre"] == 1 and r["evenements"][0]["id"] == "E02"


def test_verifier_eligibilite_ok_et_refus():
    assert outils.verifier_eligibilite("E02", 17)["eligible"] is True
    assert outils.verifier_eligibilite("E04", 30)["eligible"] is False      # complet


def test_verifier_evenement_inconnu():
    assert "erreur" in outils.verifier_eligibilite("E99", 20)


def test_creer_inscription_modifie_les_donnees():
    avant = outils.trouver_evenement("E02")["places"]
    r = outils.creer_inscription("E02", "Karim", 17)
    assert r["inscrit"] is True and r["numero"] == "INS-003"
    assert outils.trouver_evenement("E02")["places"] == avant - 1


def test_creer_inscription_refuse_un_doublon():
    r = outils.creer_inscription("E02", "Sara", 22)
    assert r["inscrit"] is False and "déjà inscrit" in r["raison"]


def test_lire_ne_modifie_rien():
    avant = json.dumps(outils.EVENEMENTS)
    outils.lister_evenements()
    outils.verifier_eligibilite("E02", 17)
    assert json.dumps(outils.EVENEMENTS) == avant


# ---------- executer_outil : jamais de plantage ----------

def test_executer_outil_normal():
    assert outils.executer_outil("verifier_eligibilite", {"id_evenement": "E02", "age": 17})["eligible"]


def test_executer_outil_argument_manquant():
    r = outils.executer_outil("verifier_eligibilite", {"id_evenement": "E02"})
    assert "erreur" in r and "age" in r["erreur"]


def test_executer_outil_age_hors_bornes():
    assert "erreur" in outils.executer_outil("verifier_eligibilite", {"id_evenement": "E02", "age": 150})


def test_executer_outil_identifiant_mal_forme():
    assert "erreur" in outils.executer_outil("verifier_eligibilite", {"id_evenement": "02", "age": 20})


def test_executer_outil_sport_inconnu():
    assert "erreur" in outils.executer_outil("lister_evenements", {"sport": "cricket"})


def test_executer_outil_inconnu():
    assert "erreur" in outils.executer_outil("supprimer_tout", {})


# ---------- Les descriptions ----------

def test_chaque_outil_a_un_schema_valide():
    noms = [s["function"]["name"] for s in outils.SCHEMAS]
    assert sorted(noms) == sorted(outils.OUTILS)
    for s in outils.SCHEMAS:
        f = s["function"]
        assert s["type"] == "function" and f["description"]
        assert set(f["parameters"]["required"]) <= set(f["parameters"]["properties"])
    json.dumps(outils.SCHEMAS)          # doit être sérialisable en JSON


def test_creer_inscription_dit_uniquement_si_demande():
    creer = [s for s in outils.SCHEMAS if s["function"]["name"] == "creer_inscription"][0]
    assert "UNIQUEMENT" in creer["function"]["description"]


def test_descriptions_vagues_ne_changent_que_les_descriptions():
    for precis, vague in zip(outils.SCHEMAS, outils.SCHEMAS_VAGUES):
        p, v = precis["function"], vague["function"]
        assert p["name"] == v["name"]
        assert len(v["description"]) < len(p["description"])
        assert p["parameters"]["required"] == v["parameters"]["required"]
        for cle, param in v["parameters"]["properties"].items():
            assert "description" not in param
            assert param["type"] == p["parameters"]["properties"][cle]["type"]
