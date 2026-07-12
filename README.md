# ApplaiNow

**ApplaiNow** - l'agent IA qui transforme votre profil/CV en offres d'emploi ciblées,
puis *(bientôt)* postule pour vous.
Construit avec **Google ADK**, **Gemini 2.5 Flash** et l'**API Adzuna**.

> Né d'une démo du premier événement du **GDG ESIEA**.

---

## Comment ça marche ?

Un pipeline en trois temps, où chaque échange transporte du **JSON structuré** (et non
du texte de chat) : le frontend peut donc afficher de vrais composants.

```
1. CV (PDF/Word/txt) ──► extraction mécanique du texte (sans LLM)
                              │
2.                       ProfileExtractionPort ──► Gemini ──► profil de recherche (JSON)
                              │                    (titres, localisations, niveau, contrat)
                        l'utilisateur ajuste le profil (formulaire)
                              │
3. Recherche :          JobSearchPort x N ──► API Adzuna   (fan-out en parallèle, SANS LLM)
                              │
                        dédoublonnage + coupe aux N meilleures
                              │
                        Comité (RH / Tech lead / Marché) ──► Gemini   (3 agents en parallèle)
                              │
                        offres annotées et notées (JSON) ──► grille de résultats
```

1. Vous **déposez votre CV** : le texte est extrait (pypdf / python-docx), puis un agent en
   déduit un **profil de recherche** structuré.
2. Vous **ajustez** ce profil (ajout d'intitulés, de localisations, choix du niveau/contrat).
3. La recherche lance **plusieurs requêtes Adzuna en parallèle** (une par couple intitulé x
   localisation), dédoublonne les offres, garde les meilleures, puis un **comité de trois
   agents** (RH, Tech lead, Marché) note et annote chaque offre selon son point de vue.

L'**entonnoir** maîtrise le coût : la recherche Adzuna ne consomme pas de LLM, et le comité
note toutes les offres retenues en un seul appel par membre. Coût typique d'un cycle complet :
**4 appels Gemini** (1 pour le profil, 3 pour le comité), quel que soit le nombre d'offres.

---

## Architecture

Deux services orchestrés par Docker Compose : un **backend Python** (ADK, architecture
hexagonale) et un **frontend Next.js** (Node/pnpm).

```
applairo/
├── docker-compose.yml         # orchestration backend + frontend
├── .env.example               # clés Google / Adzuna (lu par compose)
│
├── backend/                   # API Python - architecture hexagonale (ports & adapters)
│   ├── main.py                # point d'entrée ASGI (uvicorn)
│   ├── applairo/
│   │   ├── domain/            # cœur métier PUR (aucune dépendance technique)
│   │   │   ├── models.py      #   entités : Job, SearchProfile, ScoredJob, CommitteeScore
│   │   │   ├── errors.py      #   erreurs métier : JobSearchError, CvExtractionError, ...
│   │   │   └── ports/         #   interfaces : CvExtractor, ProfileExtraction,
│   │   │                      #                JobSearch, OfferEvaluation
│   │   ├── application/       # cas d'usage : JobSearchWorkflow (l'entonnoir)
│   │   ├── adapters/
│   │   │   ├── inbound/http/  #   entrant : FastAPI (routes /api/cv, /api/search, DTO)
│   │   │   └── outbound/
│   │   │       ├── cv/        #   sortant : DocumentCvExtractor (pypdf/python-docx)
│   │   │       ├── adzuna/    #   sortant : AdzunaJobSearch      (implémente JobSearchPort)
│   │   │       └── adk/       #   sortant : AdkProfileExtractor + AdkOfferEvaluator (comité)
│   │   ├── config.py          # configuration typée (pydantic-settings)
│   │   └── bootstrap.py       # composition root - câble les adaptateurs
│   └── Dockerfile
│
└── frontend/                  # UI Next.js (App Router)
    ├── app/
    │   ├── page.tsx           # page - monte le pipeline de recherche
    │   └── api/               # route handlers = proxy serveur vers le backend (BFF)
    │       ├── cv/            #   proxy multipart (upload du CV)
    │       └── search/        #   proxy JSON (recherche + comité)
    ├── components/            # SearchFlow, Uploader, ProfileForm, ResultsGrid, JobCard
    ├── lib/                   # api (client), backend (serveur), types
    └── Dockerfile
```

### Pourquoi hexagonal ?

Le domaine ne connaît ni ADK, ni Adzuna, ni HTTP : il définit des **ports** (interfaces),
les **adaptateurs** les implémentent. Bénéfices concrets ici :

- **ADK et Adzuna sont interchangeables** - remplacer Adzuna par France Travail = un nouvel
  adaptateur, zéro changement dans le domaine. Idem pour le modèle (extraction, comité).
- **Testable** - on peut injecter des ports factices sans réseau.
- **Scalable** - le pipeline est **sans état** : aucune session serveur. Le frontend garde le
  profil (issu de l'étape CV) et le renvoie à l'étape recherche. Chaque appel au backend est
  indépendant, donc réplicable horizontalement sans stockage partagé.
- **Coût maîtrisé** - l'entonnoir (`JobSearchWorkflow`) borne les appels LLM : fan-out Adzuna
  sans modèle, puis comité en notation par lots (un appel par membre).

---

## Prérequis

- **[Docker](https://docs.docker.com/get-docker/)** + Docker Compose *(voie recommandée)*
- Un compte **Google AI Studio** : [aistudio.google.com](https://aistudio.google.com/) *(gratuit)*
- Un compte **Adzuna Developer** : [developer.adzuna.com](https://developer.adzuna.com/) *(gratuit)*

Pour le développement local (hors Docker) : **[uv](https://docs.astral.sh/uv/)** (backend)
et **[pnpm](https://pnpm.io/)** + **Node 20** (frontend).

---

## Démarrage rapide (Docker Compose)

```bash
# 1. Configurer les clés API
cp .env.example .env      # puis renseigner GOOGLE_API_KEY + ADZUNA_APP_ID/KEY

# 2. Construire et lancer les deux services
docker compose up --build
```

| Service   | URL                             |
|-----------|---------------------------------|
| Frontend  | http://localhost:3000           |
| Backend   | http://localhost:8000 (docs `/docs`) |

> **Note Vertex AI :** en Docker, utilisez `GOOGLE_API_KEY`. Le mode Vertex (ADC) ne
> fonctionne pas dans un conteneur sans monter une clé de compte de service - voir
> les commentaires dans `.env.example`.

### Mode développement (hot reload)

Pour recharger automatiquement à chaque modification de fichier, utilisez le compose
de développement `docker-compose.dev.yml` : il monte le code source en volume et lance
les serveurs de dev (`uvicorn --reload`, `next dev`) au lieu des serveurs de production.

```bash
docker compose -f docker-compose.dev.yml up --build
```

Modifiez un `.py` ou un `.tsx` : le service concerné se recharge tout seul, sans
reconstruire l'image.

---

## Développement local (sans Docker)

### Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload    # http://localhost:8000
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev                            # http://localhost:3000
```

Le frontend appelle le backend via `BACKEND_URL` (défaut : `http://localhost:8000`).

---

## Configuration

Toute la configuration passe par des variables d'environnement (validées au démarrage
par `pydantic-settings`, voir `backend/applairo/config.py`) :

| Variable | Défaut | Rôle |
|---|---|---|
| `ADZUNA_COUNTRY` | `fr` | Pays de recherche (`fr`, `gb`, `us`, `de`, ...) |
| `RESULTS_PER_PAGE` | `15` | Nombre d'offres retournées par requête Adzuna |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modèle Gemini utilisé |
| `MAX_SEARCH_COMBOS` | `6` | Nombre max de requêtes Adzuna en fan-out (intitulé x localisation) |
| `EVAL_TOP_N` | `12` | Nombre max d'offres soumises au comité (borne le coût LLM) |
| `MAX_UPLOAD_BYTES` | `5242880` | Taille max d'un CV uploadé (5 Mo) |
| `PRICE_INPUT_USD_PER_MTOK` | `0.30` | Tarif entrée (USD/million de tokens) pour l'affichage du coût en direct |
| `PRICE_OUTPUT_USD_PER_MTOK` | `2.50` | Tarif sortie (USD/million de tokens) ; défauts = grille `gemini-2.5-flash` |
| `LOG_LEVEL` | `INFO` | `DEBUG` pour tracer les URLs/paramètres complets |

---

## Ressources pour aller plus loin

- [Documentation Google ADK](https://google.github.io/adk-docs/)
- [Documentation API Adzuna](https://developer.adzuna.com/docs/search)
- [Next.js - App Router](https://nextjs.org/docs/app)
- [Architecture hexagonale (ports & adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
