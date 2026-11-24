# FICHE DE DÉMONSTRATION — SPORTSAI

Cette fiche pas-à-pas vous permet de lancer, tester et faire la démonstration complète du projet **SportsAI** en quelques minutes.

---

## 1. Prérequis & Environnement

Le projet dispose d'un environnement virtuel configuré sous WSL (Ubuntu Linux) ou Windows.

### Ouvrir le terminal dans le projet
```bash
cd "c:\Users\Guide info\Downloads\inscription-sport\inscription-sport"
```

### Activer l'environnement virtuel (au choix selon votre terminal)

- **Dans WSL / Ubuntu bash (Recommandé)** :
  ```bash
  cd '/mnt/c/Users/Guide info/Downloads/inscription-sport/inscription-sport'
  source .venv/bin/activate
  ```

- **Dans PowerShell Windows** (si Python est installé avec les dépendances) :
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

---

## 2. Lancement du Serveur (Mode Démo / MOCK)

Le projet fonctionne **100 % hors ligne sans aucune clé API requise** grâce au mode `mock`.

### Commande de démarrage
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Une fois démarré, ouvrez votre navigateur :
- **Interface Web Interactive (UI)** : [http://localhost:8000/](http://localhost:8000/)
- **Documentation Swagger / OpenAPI** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **Vérification d'état (Health Check)** : [http://localhost:8000/health](http://localhost:8000/health)

---

## 3. Scénarios de Démonstration en Direct

### Scénario A : Assistant Intelligent & Inscription Sportive (Chat)
Testez directement dans l'interface [http://localhost:8000/](http://localhost:8000/) ou via `curl` :

1. **Consultation sans inscription** (l'agent ne doit pas inscrire) :
   > *"Quels tournois de basket sont proposés ?"*
   - **Comportement attendu** : L'agent appelle `lister_evenements`, renvoie les tournois disponibles et laisse `statut: "consulte"`.

2. **Demande d'inscription valide** :
   > *"Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim."*
   - **Comportement attendu** : L'agent vérifie l'éligibilité puis crée l'inscription (`statut: "inscrit"`).

3. **Refus métier automatique (Âge hors tranche)** :
   > *"Puis-je m'inscrire au tournoi de football ? J'ai 16 ans."*
   - **Comportement attendu** : L'agent détecte que le football est réservé aux 18 ans et plus (`statut: "refuse"` sans revue humaine).

4. **Sécurité & Protection des données (Refus pour un tiers)** :
   > *"Inscris mon ami Thomas au marathon."*
   - **Comportement attendu** : Refus déterministe immédiat pour non-respect des règles d'inscription personnelle.

---

### Scénario B : Recherche RAG dans le Règlement Sportif
Testez l'onglet **RAG** dans l'interface ou la route `/api/rag/search` :

1. **Question couverte par le règlement** :
   > *"Quels sont les délais d'annulation pour une inscription ?"*
   - **Résultat** : Réponse sourcée citant le document exact (`01_inscriptions_et_delais.md`).

2. **Question hors corpus (Gestion de l'hallucination)** :
   > *"Y a-t-il des douches chaudes et un parking gratuit sur le site ?"*
   - **Résultat** : Détection du score sous le seuil et réponse stricte : *"Je ne sais pas : les documents du règlement sportif disponibles ne contiennent pas d'information vérifiée..."*.

---

### Scénario C : Analyse & Validation Multimédia (Image & Audio)
Accessible dans la section **Multimédia** ou via `/multimedia/upload/image` et `/multimedia/upload/audio` :

1. **Test d'image valide** : Téléversez un fichier `.jpg`, `.png` ou `.webp`.
   - **Résultat** : Code HTTP 200, confirmation de la conformité et métadonnées.
2. **Test de sécurité binaire (Anti-falsification)** : Renommez un fichier texte `.txt` en `.jpg` et envoyez-le.
   - **Résultat** : Rejet immédiat avec le code **HTTP 415** (signature binaire invalide).
3. **Test de limitation de taille** : Téléversez un fichier > 5 Mo.
   - **Résultat** : Rejet automatique avec le code **HTTP 413**.

---

## 4. Commandes pour Exécuter les Tests Automatisés

Pour prouver la robustesse du projet devant un jury ou en audit technique :

```bash
# 1. Suite complète de tests unitaires (87 tests)
pytest tests/ -v

# 2. Campagne de validation multimédia (21 tests réels image/audio)
python scratch/test_multimedia_complet.py

# 3. Évaluation RAG (Recall@k et questions hors corpus)
python scratch/eval_rag.py

# 4. Évaluation de l'agent sur la matrice des 20 demandes métier
python mesures/evaluer_agent.py precises

# 5. Mesure de latence réelle (temps de réponse)
python mesures/latence.py

# 6. Comparaison statistique des prompts (descriptions précises vs vagues)
python mesures/comparer.py mock-regles__precises mock-regles__vagues
```

---

## 5. Synthèse des Résultats Clés à Présenter

- **Taux de succès des tests** : **148 / 148 (100 %)**
- **Inscriptions abusives ou non sollicitées** : **0 %** (Garde-fou déterministe actif)
- **RAG Recall@5** : **100 %** / Questions hors-corpus rejetées : **4/4**
- **Latence médiane en mode MOCK** : **~0.6 ms**
- **Rapport d'audit complet disponible** : [FINAL_TEST_REPORT.md](file:///c:/Users/Guide%20info/Downloads/inscription-sport/inscription-sport/FINAL_TEST_REPORT.md)
