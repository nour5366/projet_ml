"""ÉTAPE 1 : le contrat d'API, le mock, les codes 200 / 422 / 503."""
from fastapi.testclient import TestClient

from app import main
from app.providers import MockProvider, get_provider

client = TestClient(main.app)


class FournisseurEnPanne:
    """Simule un fournisseur distant qui plante, avec une exception qui contient un secret."""
    name = "panne"
    model = "panne"

    def appeler(self, messages, schemas):
        raise RuntimeError("clé secrète hf_abc123 dans http://adresse-interne")


def test_health_mode_mock():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["mode"] == "mock"
    assert r.json()["provider"] == "mock"
    assert r.json()["degrade"] is False


def test_assistant_200_avec_le_contrat_complet():
    r = client.post("/assistant", json={"message": "Quels tournois de basket sont proposés ?"})
    assert r.status_code == 200
    corps = r.json()
    for champ in ["provider", "model", "degrade", "latency_ms", "intention", "statut",
                  "confiance", "reponse", "actions", "requires_review", "tours", "abandon"]:
        assert champ in corps
    assert corps["provider"] == "mock"
    assert corps["latency_ms"] >= 0
    assert "E02" in corps["reponse"]


def test_texte_trop_court_rejete_422():
    assert client.post("/assistant", json={"message": "ab"}).status_code == 422


def test_champ_absent_rejete_422():
    assert client.post("/assistant", json={}).status_code == 422


def test_texte_trop_long_rejete_422():
    assert client.post("/assistant", json={"message": "a" * 501}).status_code == 422


def test_fournisseur_en_panne_donne_503_sans_secret(monkeypatch):
    monkeypatch.setattr(main, "provider", FournisseurEnPanne())
    r = client.post("/assistant", json={"message": "Quels tournois de basket sont proposés ?"})
    assert r.status_code == 503
    assert "secrète" not in r.text and "hf_abc123" not in r.text and "interne" not in r.text


def test_panne_simulee_du_mock_donne_503(monkeypatch):
    from app import config
    monkeypatch.setattr(config, "SIMULER_PANNE", True)
    r = client.post("/assistant", json={"message": "Quels tournois de basket sont proposés ?"})
    assert r.status_code == 503
    assert "panne simulée" not in r.text            # le détail reste dans les journaux


def test_repli_sur_le_mock_sans_cle():
    # Mode réel demandé mais pas de clé : on retombe sur le mock au lieu de planter.
    assert isinstance(get_provider("real"), MockProvider)


def test_le_mock_et_le_contrat_ne_citent_aucun_fournisseur():
    from pathlib import Path
    texte = (Path(__file__).parent.parent / "app" / "schemas.py").read_text(encoding="utf-8").lower()
    assert "groq" not in texte and "huggingface" not in texte
