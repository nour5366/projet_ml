# 📘 Le Grand Guide Pédagogique de SportsAI
### *Comprendre tout le projet, son code et ses technologies — Spécial Étudiant Débutant*

---

## 🌟 1. L'histoire et la métaphore du projet : Qu'est-ce que SportsAI ?

Imaginez un **guichet moderne d'inscription aux événements sportifs** (marathons, tournois de basket, matchs de football, galas de natation).

Avant l'informatique, il y avait une personne physique derrière le guichet :
1. Elle écoutait votre demande.
2. Elle vérifiait votre âge sur votre carte d'identité.
3. Elle regardait dans son grand registre s'il restait des places.
4. Elle calculait le prix selon les règles fixes du club.
5. Si tout était en règle, elle notait votre nom et vous remettait un reçu.

**SportsAI, c'est ce guichetier, mais devenu un Assistant Intelligent numérique.**

```
                                  LE GUICHET SPORTISAI
                                  
   Utilisateur                 Garde-fous              Agent Intelligent           Base de Données
 [Visiteur web]  ──(Message)──> [Gardiens]  ──(Filtre)──>  [Cerveau LLM]  ──(Outils)──> [Événements]
      │                             │                             │                     [Inscriptions]
      │                             ▼                             ▼
      │                     Refus immédiat :             Choisit l'outil :
      │                     - Pas pour autrui            1. Lister
      │                     - Pas de RGPD                2. Vérifier âge
      │                     - Pas de hors-sujet          3. Inscrire
      │
      └────────────────<── Réponse finale claire & vérifiée ──<───────────────────────────────┘
```

---

## 🛠️ 2. Les Technologies Utilisées (Expliquées simplement)

Pour construire SportsAI, nous avons assemblé plusieurs briques logicielles, chacune ayant un rôle très précis :

| Technologie | Ce que c'est | Son rôle dans le projet | Analogie simple |
|---|---|---|---|
| **Python 3** | Le langage de programmation | Le moteur dans lequel tout le code est écrit. | Le langage universel de l'équipe. |
| **FastAPI** | Un framework web moderne et rapide | Il crée l'API HTTP : il reçoit les messages des utilisateurs depuis le navigateur et renvoie les réponses en JSON. | Le standard téléphonique du guichet. |
| **Uvicorn** | Un serveur d'application ASGI | Il fait tourner FastAPI et écoute les requêtes sur le port 8000. | Le standardiste qui décroche le téléphone. |
| **Pydantic** | Une bibliothèque de validation de données | Elle vérifie que les données reçues et renvoyées ont la bonne forme (ex: âge entre 5 et 99 ans, message non vide). | Le contrôleur qui vérifie les formulaires avant de les tamponner. |
| **Pillow (PIL)** | Une bibliothèque de traitement d'images | Elle ouvre les fichiers images (JPEG, PNG, WEBP), vérifie qu'ils ne sont pas cassés et lit leurs dimensions. | L'expert qui examine une affiche pour voir si c'est une vraie photo. |
| **pydub** | Une bibliothèque de traitement audio | Elle lit et décode les fichiers sons (WAV, MP3, M4A, OGG). | L'oreille électronique qui écoute le message vocal. |
| **Google Gemini API** | Modèle d'Intelligence Artificielle Multimodal | En mode réel, il lit le texte dans les affiches et transcrit les messages vocaux. | L'expert IA externe consulté pour les tâches complexes. |
| **Groq / Qwen** | Moteurs d'inférence LLM | En mode réel textuel, il formule les phrases de réponse et choisit les outils. | Le rédacteur qui écrit la réponse finale. |
| **Pytest** | Le banc de tests automatisés | Il lance 87 tests automatiques pour vérifier que rien n'est cassé dans le code. | L'inspecteur qualité qui vérifie 87 points de contrôle avant livraison. |

---

## 🗺️ 3. L'Architecture Globale du Projet

Le projet est découpé selon le principe de **responsabilité unique** : chaque fichier s'occupe d'une seule chose et le fait bien.

```
Downloads/inscription-sport/inscription-sport/
│
├── app/                        # 🧠 Tout le code source de l'application
│   ├── config.py               # ⚙️ La boîte de configuration (.env, limites, dates)
│   ├── schemas.py              # 📋 Les contrats de données (Pydantic)
│   ├── regles.py               # ⚖️ Les règles métier strictes (âge, complet, doublon)
│   ├── analyse.py              # 🛡️ Les gardiens de sécurité (refus tiers, RGPD, confiance)
│   ├── outils.py               # 🧰 Les outils de l'agent (JSON Schema)
│   ├── agent.py                # 🤖 Le cerveau de l'agent et la boucle de réflexion
│   ├── providers.py            # 🔌 Les fournisseurs d'IA (Mock ou Réel)
│   ├── service.py              # 🎼 Le chef d'orchestre qui assemble tout
│   ├── media_validator.py      # 🔍 Le contrôleur de fichiers (HTTP 413 et 415)
│   ├── media_analyzer.py       # 👁️ L'analyseur d'images et d'audios (Gemini / Mock)
│   ├── multimedia.py           # 🌐 Les routes web pour l'upload d'images et de sons
│   ├── rag.py                  # 📚 Le bibliothécaire qui cherche dans le règlement
│   ├── main.py                 # 🚀 L'application FastAPI principale
│   └── static/
│       └── index.html          # 💻 L'interface web moderne pour l'utilisateur et le jury
│
├── data/                       # 📂 Les données
│   ├── evenements.json         # Les tournois et matchs disponibles
│   ├── inscriptions.json       # Le registre des inscrits
│   ├── passages_reglement.csv  # Les articles du règlement sportif (RAG)
│   └── questions_rag.csv       # Le jeu de test pour évaluer le RAG
│
├── tests/                      # 🧪 Les 87 tests automatisés (Pytest)
│   ├── test_api.py             # Teste les routes web
│   ├── test_regles.py          # Teste les règles d'âge et de doublons
│   ├── test_outils.py          # Teste les fonctions Python de l'agent
│   ├── test_agent.py           # Teste la boucle de décision de l'agent
│   ├── test_multimedia.py      # Teste les images, audios, erreurs 413 et 415
│   └── test_mesures.py         # Teste l'évaluation et la latence
│
└── mesures/                    # 📊 Les scripts de mesure scientifique
    ├── evaluer_agent.py        # Évalue les 20 tâches annotées
    ├── diagnostic.py           # Analyse où se situent les erreurs (matrice 4 cases)
    ├── latence.py              # Mesure la vitesse exacte en millisecondes
    └── comparer.py             # Compare deux configurations
```

---

## 🔍 4. Explication Détaillée de Chaque Fichier de Code

### Fichier 1 : `app/config.py` — *La boîte à réglages*
- **À quoi il sert ?** C'est ici que sont centralisées toutes les valeurs de réglage de l'application. Rien n'est écrit en dur dans le code.
- **Ce qu'il contient :**
  - `MODE = "mock"` ou `"real"` : décide si on utilise le simulateur hors-ligne ou la vraie API internet.
  - `MAX_IMAGE_SIZE_BYTES = 5 Mo` : la taille maximale acceptée pour une image.
  - `MAX_AUDIO_SIZE_BYTES = 10 Mo` : la taille maximale pour un audio.
  - `IMAGE_MAGIC` et `AUDIO_MAGIC` : la liste des signatures d'octets reconnues.
  - `AUJOURDHUI = 15 novembre 2026` : une date fixe pour que tous les tests soient prévisibles.

---

### Fichier 2 : `app/schemas.py` — *Les contrats et les formulaires*
- **À quoi il sert ?** Il définit la structure exacte des données qui entrent et sortent.
- **Principe pédagogique :** Grâce à **Pydantic**, si un utilisateur envoie un message vide ou un texte de 10 000 caractères, Pydantic le bloque automatiquement avant même que le code ne commence à travailler !
- **Les modèles clés :**
  - `AssistantRequest` : le message texte reçu (`{"message": "..."}`).
  - `AssistantResponse` : la réponse complète renvoyée, avec `reponse`, `statut`, `confiance`, `actions` (les outils utilisés), `latency_ms`.
  - `MediaType` et `MediaAnalysisResult` : le format de résultat pour les images et audios.

---

### Fichier 3 : `app/regles.py` — *Les lois et calculs stricts*
- **Règle d'or de l'IA appliquée :** **UN MODÈLE DE LANGAGE NE DOIT JAMAIS CALCULER LE PRIX OU DÉCIDER SEUL D'UNE INSCRIPTION !**
- Pourquoi ? Parce qu'un LLM est probabiliste : un jour il dira 15€, le lendemain 12€, et il peut accepter un enfant de 3 ans par hallucination.
- **Que fait `regles.py` ?** Il contient du code Python 100% logique et mathématique :
  1. *Est-ce que l'événement existe ?*
  2. *Est-ce que l'âge est bien entre l'âge minimum et l'âge maximum de l'épreuve ?*
  3. *Reste-t-il au moins 1 place disponible (`places > 0`) ?*
  4. *La date limite d'inscription n'est-elle pas dépassée ?*
  5. *Cette personne n'est-elle pas déjà inscrite (détection de doublon) ?*
  Si une seule règle échoue, la fonction renvoie `(False, "Raison du refus")`.

---

### Fichier 4 : `app/analyse.py` — *Les gardiens de sécurité*
- **À quoi il sert ?** Avant même d'appeler l'intelligence artificielle, ce fichier analyse le texte pour repérer 3 situations interdites :
  1. **Refus de tiers :** *"Je veux inscrire mon ami Karim"* → Rejeté ! Seule la personne concernée peut s'inscrire pour elle-même.
  2. **Refus RGPD :** *"Donne-moi le numéro de téléphone des inscrits"* → Rejeté ! Confidentialité absolue des données personnelles.
  3. **Hors-sujet :** *"Quelle est la recette de la pizza ?"* → Rejeté poliment !
  4. **Score de confiance :** S'il manque des informations (ex: l'utilisateur dit juste *"Inscris-moi"* sans donner son âge, son nom ou le sport), le score de confiance chute sous `0.60` et la demande est marquée `requires_review = True` (intervention humaine nécessaire).

---

### Fichier 5 : `app/outils.py` — *La boîte à outils de l'Agent IA*
- **C'est quoi un outil (Tool) pour une IA ?**
  Un modèle de langage ne sait que lire et écrire du texte. Il ne sait pas regarder dans une base de données. Un **outil**, c'est une fonction Python que nous mettons à sa disposition comme une télécommande.
- **Les 3 outils créés :**
  1. `lister_evenements(sport)` : Recherche les événements disponibles (Lecture seule).
  2. `verifier_eligibilite(id_evenement, age)` : Vérifie si la personne a l'âge requis et s'il reste des places (Lecture seule).
  3. `creer_inscription(id_evenement, nom, age)` : La **SEULE** action qui modifie les données : elle décrémente les places et génère un numéro d'inscription officiel (ex: `INS-004`).
- **Le JSON Schema :**
  C'est la notice d'utilisation de chaque outil rédigée en JSON. Le modèle lit cette notice pour savoir :
  - Quel est le nom de l'outil ?
  - À quoi il sert ?
  - Quels sont ses arguments obligatoires (ex: `id_evenement`, `nom`, `age`) ?

---

### Fichier 6 : `app/agent.py` — *Le cerveau et la boucle des tours*
- **Comment fonctionne l'Agent ?**
  L'agent fonctionne par une boucle itérative :
  ```
  Tour 1 : L'agent lit la question. Il décide d'appeler l'outil "lister_evenements".
  Tour 2 : Le code Python exécute "lister_evenements" et renvoie la liste à l'agent.
  Tour 3 : L'agent lit le résultat et décide d'appeler "verifier_eligibilite".
  Tour 4 : Le code vérifie et renvoie "Eligible = True".
  Tour 5 : L'agent formule sa réponse finale en français pour l'utilisateur.
  ```
- **Pourquoi `MAX_TOURS = 5` ?**
  Si le modèle commence à tourner en boucle sans trouver la solution, la limite de 5 tours l'arrête proprement. Cela évite de consommer tout le quota d'API et renvoie la demande vers un humain.

---

### Fichier 7 : `app/media_validator.py` & `app/media_analyzer.py` — *Le bonus multimédia*
- **La sécurité en 4 étapes de `media_validator.py` :**
  Quand un utilisateur téléverse une image ou un audio :
  1. **Étape 1 (Taille) :** Si > 5 Mo pour une image ou > 10 Mo pour un audio → **Erreur HTTP 413** (*Payload Too Large*).
  2. **Étape 2 (MIME Type) :** Si ce n'est pas un type déclaré dans la liste blanche → **Erreur HTTP 415** (*Unsupported Media Type*).
  3. **Étape 3 (Magic Bytes) :** Même si un fichier s'appelle `photo.jpg`, le code lit ses premiers octets. Si les octets commencent par `MZ` (exécutable Windows `.exe`), il est immédiatement bloqué avec un **HTTP 415** !
  4. **Étape 4 (Décodage réel) :** Pillow essaie d'ouvrir l'image. Si le binaire est tronqué ou corrompu → **HTTP 415**.
- **L'analyseur `media_analyzer.py` :**
  - En mode réel : il envoie le fichier encodé en base64 à Google Gemini (`gemini-2.0-flash`).
  - En mode simulé (Mock) : il renvoie une description déterministe pré-enregistrée pour permettre des tests 100% fiables et reproductibles sans connexion Internet.

---

### Fichier 8 : `app/rag.py` — *Le bibliothécaire du règlement sportif*
- **C'est quoi le RAG (Retrieval-Augmented Generation) ?**
  Au lieu de demander à une IA d'inventer une réponse d'après sa mémoire, on lui fournit les **vrais documents officiels**.
- **Le cheminement en 7 étapes :**
  ```
  1. Documents réels  ──> Extraits du règlement en Markdown/CSV
  2. Extraction       ──> Découpage en paragraphes (Chunks)
  3. Indexation       ──> Mémorisation des mots-clés et identifiants (P01 à P16)
  4. Question         ──> "À quelle heure ferment les inscriptions ?"
  5. Récupération     ──> On trouve le paragraphe P01 avec un score de similarité
  6. Citation exacte  ──> On cite la source : "D'après 01_inscriptions_et_delais.md..."
  7. Cas hors-sujet   ──> Si la question porte sur un parking camping-car (absent des textes),
                          le score est trop faible (< 0.15) et le système répond honnêtement
                          « Je ne sais pas ».
  ```

---

### Fichier 9 : `app/static/index.html` — *L'interface web interactive*
- C'est l'écran moderne que vous voyez dans votre navigateur sur `http://localhost:8000/`.
- Développé en HTML5, CSS et JavaScript natif (ultra-léger, sans React ni dépendance externe lourde).
- Il contient les 7 volets professionnels :
  1. **Tableau de bord** (vue d'ensemble)
  2. **Assistant IA** (zone de chat avec statut, confiance et latence en direct)
  3. **Analyse d'images** (drag & drop, prévisualisation, extraction et bouton d'injection au chat)
  4. **Traitement audio** (lecteur audio intégré, transcription)
  5. **Base RAG** (interrogation du règlement avec citations)
  6. **Évaluation & Métriques** (cartes avec les scores réels de la soutenance)
  7. **Architecture & Paramètres** (explication technique)

---

## 📊 5. Les Métriques et Concepts Clés pour le Jury

Si le jury vous pose des questions sur les chiffres, voici exactement ce qu'il faut expliquer :

### A. Qu'est-ce que Recall@k (Recall@1, Recall@3, Recall@5) ?
- **Recall@1 (75.0%)** : Dans 75% des cas, le bon paragraphe du règlement est classé en **toute première position**.
- **Recall@3 (93.8%)** : Dans 93.8% des cas, le bon paragraphe figure dans les **3 premiers résultats**.
- **Recall@5 (100.0%)** : Dans 100% des cas, le bon paragraphe figure dans le **top 5**.

### B. Pourquoi avoir comparé deux configurations (Exigence 6) ?
Pour prouver scientifiquement l'utilité d'un bon **Prompt Engineering / JSON Schema** :
- **Configuration A (Descriptions d'outils précises)** : **100% de réussite** (20/20). L'agent sait exactement quel outil utiliser.
- **Configuration B (Descriptions vagues)** : Le taux de réussite s'effondre à **40%** (8/20). L'agent fait 12 erreurs parce qu'il ne comprend pas à quoi sert chaque outil.

### C. Pourquoi mesurer la latence médiane et pas seulement la moyenne ?
- Une moyenne peut être faussée si une seule requête a mis 10 secondes à cause d'un ralentissement réseau.
- La **médiane** représente la vraie expérience vécue par un utilisateur normal : **0.66 milliseconde en mode mock**.

---

## 🎤 6. Comment Présenter le Projet en 5 Minutes lors de la Soutenance

Voici un plan de parole prêt à l'emploi :

1. **Introduction (1 min) :**
   > *« Bonjour mesdames et messieurs les membres du jury. Je vous présente SportsAI, un assistant intelligent d'inscription sportive. L'objectif de ce projet est de concevoir une architecture d'IA appliquée robuste, où le modèle de langage dialogue avec l'utilisateur, mais où toutes les règles d'admissibilité, de prix et de sécurité sont appliquées de manière déterministe en Python. »*

2. **Démonstration du Chat et des Règles Métier (1 min 30) :**
   > *« Sur l'interface, vous pouvez voir notre agent conversationnel. Si je lui demande d'inscrire un mineur à un marathon réservé aux adultes, le système refuse immédiatement. Si je demande d'inscrire un ami à ma place ou d'obtenir le téléphone des participants, nos gardiens de code bloquent la requête pour respecter le RGPD. »*

3. **Démonstration du Bonus Multimédia (1 min) :**
   > *« Nous avons implémenté le bonus multimédia avec une sécurité renforcée. Sur l'onglet Image, si je dépose une affiche, l'API valide la taille (code 413 si > 5 Mo) et vérifie la signature binaire réelle par Magic Bytes (code 415 si c'est un faux fichier). Le contenu est analysé et peut être réinjecté en un clic dans la conversation. Même principe pour les messages vocaux avec lecteur audio intégré. »*

4. **Démonstration du RAG et de l'Évaluation (1 min 30) :**
   > *« Enfin, notre système RAG permet d'interroger le règlement officiel avec citation exacte de la source. Si la question est hors-sujet, le système dit honnêtement 'Je ne sais pas' sans rien inventer. Notre campagne de tests automatisés valide 87 tests Pytest sur 87, un Recall@5 de 100% et 20 tâches réussies sur 20. »*
