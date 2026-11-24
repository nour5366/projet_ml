# Assistant d'inscription à des événements sportifs

Mini-projet de fin de module — Machine learning appliqué, Licence 3 DSI (version guidée en 5 étapes).

L'utilisateur écrit une phrase : « Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim. »
L'application comprend la demande, consulte les événements avec des **outils**, applique des
**règles métier**, et ne crée l'inscription que si l'utilisateur l'a **explicitement demandée**.

> Tout marche en **mode MOCK** : aucun compte, aucune clé, aucun réseau.
> Le mode réel (Groq) est un bonus facultatif, voir l'étape 4.

## 1. Installation

Ouvrez un terminal dans le dossier `inscription-sport/`. Python 3.11 ou plus récent est nécessaire.

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```
Si PowerShell refuse d'activer le venv : `Set-ExecutionPolicy -Scope Process Bypass`, puis recommencez.

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## 2. Vérifier que tout marche (hors ligne)

```bash
pytest -q
```
Résultat attendu : `67 passed` en moins de 2 secondes.

## 3. Lancer l'API

```bash
uvicorn app.main:app --reload
```
Puis ouvrez http://127.0.0.1:8000/docs : vous pouvez tester l'API directement dans le navigateur.

**Linux / macOS (curl)**
```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/assistant -H "Content-Type: application/json" \
     -d '{"message":"Quels tournois de basket sont proposés ?"}'
```

**Windows (PowerShell)**
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/assistant `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"message":"Quels tournois de basket sont proposés ?"}'
```

Codes de réponse : **200** tout va bien · **422** message invalide (trop court, trop long) ·
**503** service d'inférence indisponible (le client peut réessayer).
Pour voir un 503 : mettez `SIMULER_PANNE=1` dans `.env` puis relancez le serveur.

## 4. Essayer sans serveur

```bash
python mesures/essayer.py "Inscris-moi à E02, j'ai 17 ans, je m'appelle Karim."
```
Affiche l'analyse du message, les outils appelés, la décision et la réponse.

## 5. Les mesures

```bash
python mesures/evaluer_agent.py             # descriptions d'outils PRÉCISES
python mesures/evaluer_agent.py vagues      # descriptions VAGUES (une seule variable change)
python mesures/comparer.py                  # tableau comparatif, écart en nombre de demandes
python mesures/diagnostic.py mock-regles__vagues   # qui a échoué : outils ou rédaction ?
python mesures/seuil.py                     # choisir REVIEW_THRESHOLD par les mesures
python mesures/latence.py                   # min / médiane / max sur 20 appels
```
Les résultats JSON sont écrits dans `resultats/`.

**À lire absolument** : en mode MOCK, le « modèle » est un simulateur à règles. Les chiffres
prouvent que **votre code et vos métriques fonctionnent**, pas qu'un vrai modèle se comporte
pareil. Pour vos chiffres de soutenance, refaites les mesures avec un vrai modèle (étape 4, bonus)
et indiquez dans votre fiche d'une page quel fournisseur a produit chaque chiffre.

## 6. Où sont les 6 points essentiels ?

| # | Point essentiel | Où le voir |
|---|---|---|
| 1 | API avec contrat indépendant du fournisseur, mock + réel, clé dans `.env` | `app/schemas.py`, `app/providers.py`, `app/config.py`, `app/main.py` |
| 2 | Sortie contrainte : énumérations, bornes, règles métier qui décident | `app/schemas.py` (Sport, Intention, Statut, bornes), `app/regles.py` |
| 3 | « Je ne sais pas » : `requires_review`, seuil justifié, refus explicites | `app/service.py`, `app/analyse.py`, `mesures/seuil.py` |
| 4 | Agent : 3 outils JSON Schema, `max_tours`, aucune action non demandée | `app/outils.py`, `app/agent.py` |
| 5 | Mesurer : 20 demandes annotées + métriques écrites à la main | `data/taches.csv`, `mesures/metriques.py`, `mesures/evaluer_agent.py` |
| 6 | Comparer en changeant UNE variable : descriptions précises / vagues | `mesures/evaluer_agent.py vagues`, `mesures/comparer.py` |

Bonus couverts : **diagnostic des échecs** (`mesures/diagnostic.py`) et **latence mesurée**
(`mesures/latence.py`). Bonus non faits : multimédia (atelier 3) et RAG (atelier 4).

## 7. Les guides

Suivez-les dans l'ordre, une étape à la fois, dans le dossier `guides/` :

1. `ETAPE_1_contrat_API.md`
2. `ETAPE_2_sortie_et_je_ne_sais_pas.md`
3. `ETAPE_3_outils.md`
4. `ETAPE_4_boucle_agent.md`
5. `ETAPE_5_mesurer_comparer.md`

Puis : `FICHE_PROJET.md` (fiche d'une page à remplir), `SOUTENANCE.md` (plan de 10 minutes),
`GRILLE_AUTO_EVALUATION.md` et `MEMO.md` (commandes et vocabulaire).

## 8. Structure du projet

```
inscription-sport/
├── app/            le code de l'application
│   ├── schemas.py     le contrat d'API et les énumérations
│   ├── config.py      lecture de .env
│   ├── providers.py   MockProvider et GroqProvider
│   ├── regles.py      règles métier
│   ├── analyse.py     intention, âge, nom, confiance, refus
│   ├── outils.py      3 outils + descriptions JSON Schema
│   ├── agent.py       la boucle de l'agent
│   ├── mock_llm.py    le faux modèle (simulateur)
│   ├── service.py     assemble tout et décide du statut
│   └── main.py        routes FastAPI
├── data/           événements, inscriptions, 20 demandes annotées
├── mesures/        évaluation, comparaison, diagnostic, seuil, latence
├── tests/          67 tests, hors ligne
├── resultats/      sorties JSON des mesures
└── guides/         les 5 étapes + fiche, soutenance, grille, mémo
```

## 9. Règles de sécurité du projet

- Jamais de vraie clé dans le code. `.env` est dans `.gitignore`, `.env.example` est versionné.
- Jamais l'exception technique complète renvoyée au client : le détail reste dans les journaux.
- Le modèle ne peut jamais forcer une inscription : les règles et le garde-fou sont dans le code.
