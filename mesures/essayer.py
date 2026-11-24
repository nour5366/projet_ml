"""Essayer l'assistant en ligne de commande, sans lancer le serveur.

Usage : python mesures/essayer.py "Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim."

Affiche l'analyse du message (étape 2), les outils appelés (étapes 3 et 4) et la réponse finale.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # pour trouver le dossier app/

from app.analyse import analyser_message
from app.config import MODE
from app.providers import get_provider
from app.service import traiter_demande


def main():
    if len(sys.argv) < 2:
        print('Usage : python mesures/essayer.py "votre message"')
        return
    message = sys.argv[1]
    fournisseur = get_provider(MODE)

    analyse = analyser_message(message)
    print(f"--- Analyse (fournisseur : {fournisseur.name}) ---")
    for cle in ["intention", "sport", "id_evenement", "age", "nom", "manques", "refus", "confiance"]:
        valeur = analyse[cle].value if hasattr(analyse[cle], "value") else analyse[cle]
        print(f"{cle:<13}: {valeur}")

    sortie = traiter_demande(message, fournisseur)
    print("\n--- Outils appelés ---")
    if not sortie["actions"]:
        print("(aucun)")
    for a in sortie["actions"]:
        print(f"{a['outil']}({json.dumps(a['arguments'], ensure_ascii=False)})")
    print(f"\n--- Décision : statut={sortie['statut'].value}, "
          f"requires_review={sortie['requires_review']}, tours={sortie['tours']} ---")
    print(sortie["reponse"])


if __name__ == "__main__":
    main()
