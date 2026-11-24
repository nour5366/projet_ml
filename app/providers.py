"""Les fournisseurs : deux classes qui ont la MÊME méthode `appeler`.

Le reste de l'application ne sait pas laquelle est utilisée.
"""
import time

from app import config, mock_llm
from app.config import GROQ_API_KEY, MODEL_ID, PAUSE_GROQ


class MockProvider:
    """Hors ligne, sans clé, toujours la même réponse. Ne prouve rien sur la qualité d'un vrai modèle."""
    name = "mock"
    model = "mock-regles"

    def appeler(self, messages, schemas):
        if config.SIMULER_PANNE:               # SIMULER_PANNE=1 dans .env : on provoque un 503
            raise RuntimeError("panne simulée du fournisseur")
        return mock_llm.repondre(messages, schemas)


class GroqProvider:
    """Le vrai modèle, appelé à distance. Seul le backend connaît la clé."""
    name = "groq"

    def __init__(self, modele=None):
        from groq import Groq          # import ICI : inutile en mode MOCK
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY absente")
        self.model = modele or MODEL_ID
        self.client = Groq(api_key=GROQ_API_KEY)

    def appeler(self, messages, schemas):
        from groq import RateLimitError
        for essai in range(2):
            try:
                reponse = self.client.chat.completions.create(
                    model=self.model, temperature=0.0,
                    messages=messages, tools=schemas, tool_choice="auto")
                time.sleep(PAUSE_GROQ)         # reste sous 30 requêtes/minute
                return reponse.choices[0].message
            except RateLimitError:
                if essai == 1:
                    raise
                time.sleep(20)                 # quota atteint : on attend puis on réessaie une fois


def get_provider(mode, modele=None):
    """mode "real" + clé valide -> GroqProvider ; sinon repli sur le mock (visible via `degrade`)."""
    if mode == "real":
        try:
            return GroqProvider(modele)
        except Exception:
            return MockProvider()              # repli automatique
    return MockProvider()
