"""Mesure la latence sur 20 appels : minimum, médiane, maximum.

Usage : python mesures/latence.py
(En mode MOCK les durées sont minuscules ; en mode réel elles se comptent en secondes.)
"""
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # pour trouver le dossier app/

from app import outils
from app.config import MODE
from app.providers import get_provider
from app.service import traiter_demande
from evaluer_agent import charger_taches


def main():
    fournisseur = get_provider(MODE)
    demandes = [t["demande"] for t in charger_taches()]     # exactement 20 demandes
    durees = []
    for demande in demandes:
        outils.recharger_donnees()
        debut = time.perf_counter()
        traiter_demande(demande, fournisseur)
        durees.append((time.perf_counter() - debut) * 1000)   # en millisecondes

    print(f"fournisseur : {fournisseur.name} ({fournisseur.model}) - {len(durees)} appels")
    print(f"minimum : {min(durees):.2f} ms")
    print(f"médiane : {statistics.median(durees):.2f} ms")
    print(f"maximum : {max(durees):.2f} ms")
    print(f"moyenne : {statistics.mean(durees):.2f} ms")
    print("\nPourquoi la moyenne seule est trompeuse : un seul appel très lent (réseau saturé,")
    print("quota atteint) tire la moyenne vers le haut alors que la plupart des appels sont rapides.")
    print("La médiane dit ce que vit un utilisateur typique ; le maximum dit le pire cas.")


if __name__ == "__main__":
    main()
