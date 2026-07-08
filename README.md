# Applairo

**Applairo** - l'agent IA qui transforme votre profil/CV en offres d'emploi ciblées,
puis *(bientôt)* postule pour vous.
Construit avec **Google ADK**, **Gemini 2.5 Flash** et l'**API Adzuna**.

> Né d'une démo du premier événement du **GDG ESIEA**.

---

## Comment ça marche ?

```
Navigateur ──► Frontend Next.js ──► Backend FastAPI ──► Agent ADK (Gemini 2.5 Flash)
 (chat +        (proxy /api,          (hexagonal)              │
  panneau        pas de CORS)                        pose 4 questions
  profil)                                                      │
                                                     profil complet
                                                              │
                                                     JobSearchPort ──► API Adzuna
                                                              │
                                                       offres d'emploi
```

1. L'agent pose **4 questions** pour construire votre profil (poste, ville, expérience, contrat)
2. Dès le profil complet, il appelle automatiquement l'outil `search_jobs`
3. L'outil délègue au `JobSearchPort`, implémenté par l'adaptateur Adzuna (une requête HTTP)
4. Les offres s'affichent dans le chat en markdown

Le panneau latéral montre **en temps réel** les informations collectées - c'est l'aspect
pédagogique de la démo.

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
│   │   │   ├── models.py      #   entités : Job, SearchCriteria
│   │   │   ├── errors.py      #   erreurs métier : JobSearchError
│   │   │   └── ports/         #   interfaces : JobSearchPort, ConversationPort
│   │   ├── application/       # cas d'usage : ChatService
│   │   ├── adapters/
│   │   │   ├── inbound/http/  #   entrant : FastAPI (routes, schémas DTO)
│   │   │   └── outbound/
│   │   │       ├── adzuna/    #   sortant : AdzunaJobSearch  (implémente JobSearchPort)
│   │   │       └── adk/       #   sortant : AdkConversation  (implémente ConversationPort)
│   │   ├── config.py          # configuration typée (pydantic-settings)
│   │   └── bootstrap.py       # composition root - câble les adaptateurs
│   └── Dockerfile
│
└── frontend/                  # UI Next.js (App Router)
    ├── app/
    │   ├── page.tsx           # page - monte le chat
    │   └── api/               # route handlers = proxy serveur vers le backend (BFF)
    ├── components/            # Chat, ProfilePanel
    ├── lib/                   # api (client), backend (serveur), profile, types
    └── Dockerfile
```

### Pourquoi hexagonal ?

Le domaine ne connaît ni ADK, ni Adzuna, ni HTTP : il définit des **ports** (interfaces),
les **adaptateurs** les implémentent. Bénéfices concrets ici :

- **ADK et Adzuna sont interchangeables** - remplacer Adzuna par France Travail = un nouvel
  adaptateur, zéro changement dans le domaine.
- **Testable** - on peut injecter des ports factices sans réseau.
- **Scalable** - les sessions passent par le `SessionService` d'ADK, injecté dans le
  `bootstrap`. En V1 c'est `InMemorySessionService` (mono-instance) ; pour un scaling
  horizontal, injecter `DatabaseSessionService` - rien d'autre à changer.

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
| `RESULTS_PER_PAGE` | `15` | Nombre d'offres retournées |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modèle Gemini utilisé |

---

## Ressources pour aller plus loin

- [Documentation Google ADK](https://google.github.io/adk-docs/)
- [Documentation API Adzuna](https://developer.adzuna.com/docs/search)
- [Next.js - App Router](https://nextjs.org/docs/app)
- [Architecture hexagonale (ports & adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
