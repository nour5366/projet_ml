"""ÉTAPE 5 : métriques, diagnostic, jeu de test et comparaison d'une seule variable."""
import csv

import evaluer_agent
from app.config import DATA_DIR
from diagnostic import diagnostic
from metriques import (bons_outils, erreurs_de_revue, inscriptions_non_demandees,
                       reponse_juste, separer, tentatives_bloquees)


# ---------- Métriques écrites à la main ----------

def test_separer():
    assert separer("a;b") == ["a", "b"] and separer("") == []


def test_bons_outils():
    assert bons_outils(["verifier_eligibilite"], ["verifier_eligibilite"])
    assert not bons_outils(["verifier_eligibilite"], ["creer_inscription"])
    assert bons_outils([], [])


def test_consultation_toleree():
    assert bons_outils(["verifier_eligibilite"], ["lister_evenements", "verifier_eligibilite"], True)
    assert not bons_outils(["verifier_eligibilite"], ["lister_evenements", "verifier_eligibilite"], False)
    assert not bons_outils(["verifier_eligibilite"], ["lister_evenements", "creer_inscription"], True)


def test_reponse_juste_normalise_et_accepte_les_formes():
    assert reponse_juste("L'âge (25 ans) est hors de la TRANCHE", "tranche")
    assert reponse_juste("Prix : 15 euros", "15 euros|quinze euros")
    assert reponse_juste("E02 : 15 euros", "E02;15 euros")
    assert not reponse_juste("E02 : 15 euros", "E02;20 euros")      # un fait manque
    assert reponse_juste("n'importe quoi", "")                      # aucun fait demandé


def test_inscriptions_non_demandees():
    creee = [{"outil": "creer_inscription", "resultat": {"inscrit": True}}]
    bloquee = [{"outil": "creer_inscription", "resultat": {"bloque": True}}]
    assert inscriptions_non_demandees(creee, demande_inscription=False) == 1
    assert inscriptions_non_demandees(creee, demande_inscription=True) == 0
    assert inscriptions_non_demandees(bloquee, demande_inscription=False) == 0
    assert tentatives_bloquees(bloquee, demande_inscription=False) == 1


def test_erreurs_de_revue():
    assert erreurs_de_revue([1, 0, 1, 0], [1, 1, 0, 0]) == (1, 1)


# ---------- Diagnostic 2 x 2 ----------

def test_diagnostic_quatre_cases():
    cases = diagnostic([True, True, False, False], [True, False, True, False])
    assert cases == {"ok": [0], "redaction": [1], "detour": [2], "outils": [3]}


def test_diagnostic_somme_egale_nombre_de_demandes():
    cases = diagnostic([True, False, True, False, True], [True, True, False, False, True])
    assert sum(len(v) for v in cases.values()) == 5


# ---------- Le jeu de test ----------

def lire_taches():
    with open(DATA_DIR / "taches.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_jeu_de_test_20_demandes_avec_cas_difficiles_et_cas_a_refuser():
    taches = lire_taches()
    assert len(taches) == 20
    assert len({t["id"] for t in taches}) == 20
    types = [t["type"] for t in taches]
    assert types.count("difficile") >= 5 and types.count("refus") >= 4
    assert sum(1 for t in taches if t["outils_attendus"] == "") >= 5     # demandes SANS outil


def test_le_mock_reussit_les_20_demandes_et_ne_cree_rien_sans_demande(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluer_agent, "RESULTATS_DIR", tmp_path)
    resume, _ = evaluer_agent.evaluer("precises")
    assert resume["nb_taches"] == 20 and resume["reussies"] == 20
    assert resume["inscriptions_non_demandees"] == 0 and resume["abandons"] == 0
    assert (tmp_path / "mock-regles__precises.json").exists()


def test_une_seule_variable_change_les_descriptions_vagues_font_baisser_le_score(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluer_agent, "RESULTATS_DIR", tmp_path)
    precises, _ = evaluer_agent.evaluer("precises")
    vagues, _ = evaluer_agent.evaluer("vagues")
    assert precises["reussies"] - vagues["reussies"] >= 3      # écart mesurable (règle des 3 demandes)
