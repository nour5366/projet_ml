"""Réglages communs aux tests : toujours hors ligne, toujours des données propres."""
import os

# Avant tout import de l'application : on force le mode MOCK, sans clé.
os.environ["INFERENCE_MODE"] = "mock"
os.environ["GROQ_API_KEY"] = ""
os.environ["REVIEW_THRESHOLD"] = "0.60"
# Délais réduits pour accélérer l'exécution de la suite de tests automatisés
os.environ.setdefault("GEMINI_BACKOFF_DELAYS", "0.001,0.002,0.004,0.008")

import pytest  # noqa: E402

from app import outils  # noqa: E402


@pytest.fixture(autouse=True)
def donnees_propres():
    """Chaque test repart des mêmes événements et des mêmes inscriptions."""
    outils.recharger_donnees()
