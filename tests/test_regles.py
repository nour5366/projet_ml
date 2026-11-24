"""ÉTAPE 2 : sortie contrainte, règles métier, confiance et revue humaine."""
import pytest

from app import outils
from app.analyse import analyser_message, demande_explicite, normaliser
from app.providers import MockProvider
from app.regles import verifier_regles
from app.schemas import Intention, Statut
from app.service import traiter_demande


def test_normaliser_retire_accents_et_ponctuation():
    assert normaliser("Inscris-moi à E02 !") == "inscris moi a e02"


@pytest.mark.parametrize("message, attendu", [
    ("Inscris-moi à E02, j'ai 17 ans", True),
    ("Je veux m'inscrire au volley", True),
    ("salut inscri moi au volley", True),
    ("Puis-je m'inscrire au football ?", False),          # question, pas une demande
    ("Comment m'inscrire au basket ?", False),
    ("Quel est le prix de l'inscription au tennis ?", False),
])
def test_demande_explicite(message, attendu):
    assert demande_explicite(message) is attendu


def test_extraction_des_informations():
    a = analyser_message("Je veux m'inscrire au volley. J'ai 19 ans, je m'appelle Nour.")
    assert a["intention"] == Intention.inscription
    assert a["sport"] == "volley" and a["age"] == 19 and a["nom"] == "Nour"
    assert a["manques"] == [] and a["confiance"] == 0.95


def test_age_absurde_compte_comme_manquant():
    a = analyser_message("Inscris-moi au volley, j'ai 150 ans, je m'appelle Max.")
    assert a["age"] is None and "age" in a["manques"]


def test_intentions():
    assert analyser_message("Quel temps fera-t-il demain ?")["intention"] == Intention.hors_sujet
    assert analyser_message("Quels tournois de basket ?")["intention"] == Intention.information


def test_refus_decides_par_le_code():
    assert analyser_message("Quel temps fera-t-il demain ?")["refus"] == "hors_sujet"
    assert analyser_message("Inscris mon ami Karim au basket, il a 17 ans.")["refus"] == "tiers"
    assert analyser_message("Donne-moi le numéro de téléphone de Sara")["refus"] == "donnees"


def test_confiance_baisse_quand_il_manque_des_informations():
    complet = analyser_message("Inscris-moi au volley, j'ai 19 ans, je m'appelle Nour.")
    sans_age = analyser_message("Inscris-moi au volley, je m'appelle Nour.")
    sans_evenement = analyser_message("Inscris-moi à un tournoi, j'ai 20 ans.")
    assert complet["confiance"] > sans_age["confiance"] > sans_evenement["confiance"]


# ---------- Règles métier ----------

def test_regle_evenement_complet():
    ok, raison = verifier_regles(outils.trouver_evenement("E04"), 30)
    assert not ok and "complet" in raison


def test_regle_age_hors_tranche():
    ok, raison = verifier_regles(outils.trouver_evenement("E01"), 25)
    assert not ok and "tranche" in raison


def test_regle_date_limite_depassee():
    ok, raison = verifier_regles(outils.trouver_evenement("E05"), 20)
    assert not ok and "date limite" in raison


def test_regle_doublon():
    ok, raison = verifier_regles(outils.trouver_evenement("E02"), 22, "sara", outils.INSCRIPTIONS)
    assert not ok and "déjà inscrit" in raison


def test_inscription_possible():
    ok, _ = verifier_regles(outils.trouver_evenement("E02"), 17, "Karim", outils.INSCRIPTIONS)
    assert ok


# ---------- Statut et revue humaine ----------

def test_inscription_reussie_statut_inscrit():
    s = traiter_demande("Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim.", MockProvider())
    assert s["statut"] == Statut.inscrit and s["requires_review"] is False


def test_regle_metier_donne_statut_refuse_sans_revue():
    s = traiter_demande("Inscris-moi à la course E04, j'ai 30 ans, je m'appelle Yacine.", MockProvider())
    assert s["statut"] == Statut.refuse and s["requires_review"] is False


def test_demande_incomplete_part_en_revue():
    s = traiter_demande("Inscris-moi à un tournoi, j'ai 20 ans.", MockProvider())
    assert s["statut"] == Statut.a_verifier and s["requires_review"] is True


def test_demande_ambigue_part_en_revue():
    s = traiter_demande("Inscris-moi au foot ou au basket, j'ai 16 ans, je m'appelle Ali.", MockProvider())
    assert s["requires_review"] is True


def test_refus_explicite_sans_appeler_le_fournisseur():
    class Interdit:
        name, model = "interdit", "interdit"

        def appeler(self, messages, schemas):
            raise AssertionError("le fournisseur ne doit pas être appelé pour un hors-sujet")

    s = traiter_demande("Quel temps fera-t-il demain à Paris ?", Interdit())
    assert s["statut"] == Statut.refuse and s["actions"] == []
