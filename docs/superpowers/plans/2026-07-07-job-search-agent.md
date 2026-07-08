# Job Search Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire un agent conversationnel Google ADK qui collecte le profil d'un utilisateur en 5 questions, interroge l'API Adzuna, et affiche les offres d'emploi correspondantes dans une interface Gradio.

**Architecture:** Un `LlmAgent` Google ADK (Gemini 2.0 Flash) guide la collecte du profil via son prompt système, puis appelle un outil Python `search_jobs` qui wrape l'API Adzuna. L'interface Gradio `ChatInterface` sert de frontend et maintient l'historique de la session.

**Tech Stack:** `google-adk`, `gradio`, `requests`, `python-dotenv`, Adzuna API, Gemini 2.0 Flash

---

## Fichiers à créer

| Fichier | Rôle |
|---|---|
| `requirements.txt` | Dépendances Python du projet |
| `.env.example` | Template des variables d'environnement (sans valeurs) |
| `.gitignore` | Exclure `.env` et les fichiers générés |
| `config.py` | Constantes du projet (RESULTS_PER_PAGE, pays) |
| `tools/__init__.py` | Rend `tools/` un package Python |
| `tools/adzuna.py` | Outil `search_jobs` — wrapper de l'API Adzuna |
| `agent.py` | Définition du `LlmAgent` ADK et du prompt système |
| `app.py` | Interface Gradio — point d'entrée de l'application |
| `README.md` | Documentation pour les participants GDG |

---

## Task 1 : Setup du projet

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config.py`

- [ ] **Step 1 : Créer `requirements.txt`**

```
google-adk>=1.0.0
gradio>=4.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

- [ ] **Step 2 : Créer `.env.example`**

```
# Clé API Google (pour Gemini) — obtenir sur https://aistudio.google.com/
GOOGLE_API_KEY=your_google_api_key_here

# Identifiants Adzuna — créer un compte sur https://developer.adzuna.com/
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
```

- [ ] **Step 3 : Créer `.gitignore`**

```
# Variables d'environnement (NE JAMAIS COMMITTER CE FICHIER)
.env

# Environnement virtuel Python
.venv/
venv/
__pycache__/
*.pyc
*.pyo

# Fichiers IDE
.vscode/
.idea/

# Fichiers système
.DS_Store
```

- [ ] **Step 4 : Créer `config.py`**

```python
# config.py
# Constantes globales du projet Job Search Agent.
# Modifier RESULTS_PER_PAGE pour contrôler le nombre d'offres retournées.

# Nombre maximum d'offres retournées par l'API Adzuna lors d'une recherche
RESULTS_PER_PAGE = 15

# Code pays pour l'API Adzuna (fr = France)
# Autres options : gb, us, de, au, ca, nl, nz, pl, ru, za
ADZUNA_COUNTRY = "fr"
```

- [ ] **Step 5 : Installer les dépendances**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

Résultat attendu : installation sans erreur, `pip list` affiche `google-adk`, `gradio`, `requests`, `python-dotenv`.

- [ ] **Step 6 : Copier `.env.example` en `.env` et remplir les clés**

```bash
cp .env.example .env
# Ouvrir .env et remplacer les valeurs par vos vraies clés API
```

---

## Task 2 : Outil de recherche Adzuna

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/adzuna.py`

- [ ] **Step 1 : Créer `tools/__init__.py`**

```python
# tools/__init__.py
# Package contenant les outils (tools) utilisés par l'agent ADK.
# Chaque outil est une fonction Python que l'agent peut appeler
# pour interagir avec des APIs ou des services externes.
```

- [ ] **Step 2 : Créer `tools/adzuna.py`**

```python
# tools/adzuna.py
# Outil de recherche d'emploi via l'API Adzuna.
#
# Cet outil est enregistré auprès de l'agent ADK : quand l'agent
# décide de lancer une recherche, il appelle la fonction search_jobs()
# avec les informations collectées auprès de l'utilisateur.
#
# Documentation API Adzuna : https://developer.adzuna.com/docs/search

import os
import requests
from config import RESULTS_PER_PAGE, ADZUNA_COUNTRY


def search_jobs(
    title: str,
    location: str,
    experience: str,
    skills: str,
    contract_type: str,
) -> str:
    """Recherche des offres d'emploi sur Adzuna selon le profil de l'utilisateur.

    Cette fonction est appelée automatiquement par l'agent une fois que
    les 5 informations du profil ont été collectées.

    Args:
        title: Intitulé du poste recherché (ex: "Développeur Python")
        location: Ville ou région souhaitée (ex: "Paris", "Lyon")
        experience: Niveau d'expérience (ex: "junior", "senior")
        skills: Compétences clés séparées par des virgules (ex: "Python, Django, SQL")
        contract_type: Type de contrat souhaité (ex: "CDI", "stage")

    Returns:
        Chaîne markdown formatée listant les offres trouvées,
        ou un message d'erreur si la recherche échoue.
    """
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        return (
            "Erreur de configuration : les clés API Adzuna sont manquantes. "
            "Vérifiez que ADZUNA_APP_ID et ADZUNA_APP_KEY sont définis dans votre fichier .env."
        )

    # L'API Adzuna (tier gratuit) n'a pas de filtre contract_type dédié.
    # On injecte toutes les informations dans le champ `what` pour une
    # recherche sémantique (ex: "développeur python senior stage Paris").
    what_query = f"{title} {skills} {experience} {contract_type}".strip()

    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": what_query,
        "where": location,
        "results_per_page": RESULTS_PER_PAGE,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        return "Erreur : impossible de joindre l'API Adzuna. Vérifiez votre connexion internet."
    except requests.exceptions.HTTPError as e:
        return f"Erreur API Adzuna ({e.response.status_code}) : vérifiez vos clés API."
    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la recherche : {e}"

    results = data.get("results", [])

    if not results:
        return (
            f"Aucune offre trouvée pour « {title} » à « {location} ».\n\n"
            "Suggestions pour élargir votre recherche :\n"
            "- Essayez une ville plus grande ou une région\n"
            "- Simplifiez l'intitulé du poste\n"
            "- Réduisez le nombre de compétences"
        )

    output = f"**{len(results)} offres trouvées pour « {title} » à « {location} »**\n\n"
    output += "---\n\n"

    for i, job in enumerate(results, 1):
        job_title = job.get("title", "Poste non précisé")
        company = job.get("company", {}).get("display_name", "Entreprise non précisée")
        job_location = job.get("location", {}).get("display_name", location)
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        job_url = job.get("redirect_url", "#")

        # Formatage du salaire uniquement si disponible
        if salary_min and salary_max:
            salary_str = f"💰 {int(salary_min):,} – {int(salary_max):,} €/an\n"
        elif salary_min:
            salary_str = f"💰 À partir de {int(salary_min):,} €/an\n"
        else:
            salary_str = ""

        output += f"### {i}. {job_title}\n"
        output += f"🏢 **{company}**\n"
        output += f"📍 {job_location}\n"
        output += salary_str
        output += f"🔗 [Voir l'offre]({job_url})\n\n"

    return output
```

- [ ] **Step 3 : Valider l'outil manuellement**

Dans un terminal Python (`.venv` activé, `.env` rempli) :

```python
from dotenv import load_dotenv
load_dotenv()
from tools.adzuna import search_jobs
print(search_jobs("développeur python", "Paris", "junior", "Python Django", "CDI"))
```

Résultat attendu : liste d'offres en markdown, ou message d'erreur explicite si les clés sont invalides.

---

## Task 3 : Agent ADK

**Files:**
- Create: `agent.py`

- [ ] **Step 1 : Créer `agent.py`**

```python
# agent.py
# Définition de l'agent conversationnel Job Search.
#
# Google ADK (Agent Development Kit) permet de créer des agents IA
# capables d'utiliser des outils (fonctions Python) et de maintenir
# une conversation structurée avec l'utilisateur.
#
# L'agent utilise Gemini 2.0 Flash comme modèle de langage et
# l'outil search_jobs pour interroger l'API Adzuna.

from google.adk.agents import LlmAgent
from tools.adzuna import search_jobs

# Le prompt système définit le comportement et la personnalité de l'agent.
# Il guide le LLM pour poser les questions dans le bon ordre et
# déclencher la recherche au bon moment.
SYSTEM_PROMPT = """Tu es JobBot, un assistant de recherche d'emploi créé pour le GDG ESIEA.
Tu aides les utilisateurs à trouver des offres d'emploi adaptées à leur profil.

## Ta mission

Collecter 5 informations sur l'utilisateur, puis lancer automatiquement une recherche d'emploi.

## Protocole de collecte (OBLIGATOIRE)

Pose ces questions UNE PAR UNE, dans cet ordre exact. N'en pose JAMAIS deux en même temps.

1. **Poste recherché** — demande l'intitulé du poste (ex: Développeur Python, Data Scientist, Chef de projet)
2. **Localisation** — demande la ville ou la région souhaitée
3. **Niveau d'expérience** — propose clairement les 3 options : junior / intermédiaire / senior
4. **Compétences clés** — demande les principales technologies ou compétences (ex: Python, React, SQL)
5. **Type de contrat** — propose les options : CDI / CDD / stage / alternance

## Après la collecte

Dès que tu as les 5 informations, appelle IMMÉDIATEMENT l'outil search_jobs sans attendre de confirmation.
Annonce que tu lances la recherche, puis présente les résultats de façon enthousiaste.

## Ton style

- Accueille chaleureusement l'utilisateur avec une courte présentation (2 phrases max)
- Sois concis et professionnel
- Si une réponse est ambiguë, demande une clarification avant de passer à la question suivante
- Après les résultats, propose de relancer une recherche avec des critères différents
"""

# Création de l'agent ADK
# - name : identifiant unique de l'agent
# - model : modèle Gemini à utiliser (gemini-2.0-flash = rapide et efficace)
# - instruction : le prompt système qui guide le comportement de l'agent
# - tools : liste des fonctions Python que l'agent peut appeler
root_agent = LlmAgent(
    name="job_search_agent",
    model="gemini-2.0-flash",
    description="Agent conversationnel de recherche d'emploi pour le GDG ESIEA",
    instruction=SYSTEM_PROMPT,
    tools=[search_jobs],
)
```

- [ ] **Step 2 : Vérifier que l'agent se crée sans erreur**

```bash
python -c "from agent import root_agent; print('Agent OK:', root_agent.name)"
```

Résultat attendu : `Agent OK: job_search_agent`

---

## Task 4 : Interface Gradio

**Files:**
- Create: `app.py`

- [ ] **Step 1 : Créer `app.py`**

```python
# app.py
# Point d'entrée de l'application Job Search Agent.
#
# Ce fichier lance l'interface web Gradio et connecte l'agent ADK
# au chat. Chaque message de l'utilisateur est transmis à l'agent
# qui maintient l'historique de la conversation en session.
#
# Lancement : python app.py
# Interface disponible sur : http://localhost:7860

import os
import asyncio
import uuid
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
# Doit être fait AVANT d'importer l'agent (qui utilise GOOGLE_API_KEY)
load_dotenv()

import gradio as gr
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agent import root_agent

# --- Configuration de la session ADK ---
# InMemorySessionService stocke l'historique de la conversation en mémoire.
# Chaque utilisateur reçoit un session_id unique pour isoler ses échanges.
APP_NAME = "job_search_agent"
session_service = InMemorySessionService()


async def initialize_session(session_id: str) -> None:
    """Crée une nouvelle session ADK pour un utilisateur."""
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )


async def chat_with_agent(message: str, history: list, session_id: str) -> str:
    """Transmet un message à l'agent ADK et retourne sa réponse.

    Args:
        message: Le message envoyé par l'utilisateur dans le chat
        history: Historique de la conversation (géré par Gradio)
        session_id: Identifiant unique de la session utilisateur

    Returns:
        La réponse textuelle de l'agent en markdown
    """
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    user_content = Content(role="user", parts=[Part(text=message)])

    response_text = ""
    async for event in runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text

    return response_text


def create_chat_handler(session_id: str):
    """Crée un handler de chat lié à une session spécifique."""

    async def handler(message: str, history: list) -> str:
        return await chat_with_agent(message, history, session_id)

    return handler


def on_new_session() -> tuple[str, list]:
    """Initialise une nouvelle session quand un utilisateur ouvre l'interface.

    Returns:
        Tuple (session_id, historique vide)
    """
    session_id = str(uuid.uuid4())
    asyncio.get_event_loop().run_until_complete(initialize_session(session_id))
    return session_id, []


# --- Construction de l'interface Gradio ---
with gr.Blocks(title="Job Search Agent — GDG ESIEA") as demo:
    gr.Markdown(
        """
        # 🔍 Job Search Agent
        **GDG ESIEA** — Propulsé par Google ADK + Gemini 2.0 Flash + Adzuna

        Discutez avec votre assistant IA pour trouver les offres d'emploi qui correspondent à votre profil.
        """
    )

    # État de session : chaque onglet/utilisateur a son propre session_id
    session_state = gr.State(value="")

    chatbot = gr.ChatInterface(
        fn=lambda msg, hist: None,  # Remplacé dynamiquement par on_load
        type="messages",
        chatbot=gr.Chatbot(height=500, type="messages"),
        textbox=gr.Textbox(
            placeholder="Tapez votre message ici...",
            container=False,
        ),
    )

    # Initialisation de la session au chargement de la page
    demo.load(
        fn=on_new_session,
        outputs=[session_state, chatbot.chatbot],
    )


if __name__ == "__main__":
    # Vérification des clés API au démarrage
    missing_keys = []
    for key in ["GOOGLE_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY"]:
        if not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        print(f"⚠️  Clés API manquantes dans .env : {', '.join(missing_keys)}")
        print("Copiez .env.example en .env et remplissez les valeurs.")
        exit(1)

    print("✅ Clés API détectées")
    print("🚀 Démarrage de l'interface sur http://localhost:7860")
    demo.launch(share=False)
```

> **Note pour l'implémentation :** L'intégration Gradio + ADK nécessite d'adapter le handler de chat pour lier dynamiquement la session. Si `ChatInterface` ne supporte pas directement le `session_id` via `gr.State`, utiliser `gr.Blocks` avec un `gr.Chatbot` + `gr.Button` en mode manuel (voir étape suivante).

- [ ] **Step 2 : Tester le lancement**

```bash
python app.py
```

Résultat attendu : 
```
✅ Clés API détectées
🚀 Démarrage de l'interface sur http://localhost:7860
Running on local URL: http://127.0.0.1:7860
```

- [ ] **Step 3 : Valider le parcours complet dans le navigateur**

Ouvrir `http://localhost:7860` et vérifier :
1. L'agent accueille l'utilisateur avec une présentation
2. Il pose les 5 questions une par une (poste → localisation → expérience → compétences → contrat)
3. Après la 5ème réponse, il annonce le lancement de la recherche
4. Les offres s'affichent en markdown avec titres, entreprises, localisations, salaires et liens

---

## Task 5 : README et documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1 : Créer `README.md`**

```markdown
# Job Search Agent — GDG ESIEA

Agent conversationnel IA qui trouve des offres d'emploi adaptées à votre profil.
Construit avec **Google ADK**, **Gemini 2.0 Flash** et l'**API Adzuna**.

Développé dans le cadre du premier événement du GDG ESIEA.

---

## Architecture

```
job-search-agent/
├── agent.py          # LlmAgent ADK (logique conversationnelle + prompt)
├── tools/
│   └── adzuna.py     # Outil search_jobs (appels API Adzuna)
├── app.py            # Interface web Gradio
├── config.py         # Constantes configurables
├── requirements.txt  # Dépendances Python
└── .env.example      # Template des variables d'environnement
```

**Flux de données :**
1. L'utilisateur répond à 5 questions dans le chat
2. L'agent appelle l'outil `search_jobs` avec le profil collecté
3. L'outil interroge l'API Adzuna (une seule requête HTTP)
4. Les offres sont affichées en markdown dans le chat

---

## Prérequis

- Python 3.10+
- Un compte Google AI Studio → [aistudio.google.com](https://aistudio.google.com/) (gratuit)
- Un compte Adzuna Developer → [developer.adzuna.com](https://developer.adzuna.com/) (gratuit)

---

## Installation

**1. Cloner le repo et créer l'environnement virtuel**

```bash
git clone <url-du-repo>
cd GDG_ESIEA_AI_AGENT
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

**2. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**3. Configurer les clés API**

```bash
cp .env.example .env
```

Ouvrir `.env` et remplir :
- `GOOGLE_API_KEY` : obtenir sur [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- `ADZUNA_APP_ID` et `ADZUNA_APP_KEY` : obtenir sur [developer.adzuna.com](https://developer.adzuna.com/)

---

## Lancement

```bash
python app.py
```

L'interface est disponible sur **http://localhost:7860**

---

## Configuration

Modifier `config.py` pour ajuster le comportement :

```python
RESULTS_PER_PAGE = 15  # Nombre d'offres retournées (défaut: 15)
ADZUNA_COUNTRY = "fr"  # Pays de recherche (fr, gb, us, de...)
```

---

## Ressources

- [Documentation Google ADK](https://google.github.io/adk-docs/)
- [API Adzuna](https://developer.adzuna.com/docs/search)
- [Documentation Gradio](https://www.gradio.app/docs)
```

---

## Self-Review

### Couverture du spec

| Exigence spec | Tâche |
|---|---|
| Google ADK Python | Task 3 — `agent.py` |
| Gemini 2.0 Flash | Task 3 — paramètre `model` |
| API Adzuna (FR) | Task 2 — `tools/adzuna.py` |
| Interface Gradio | Task 4 — `app.py` |
| 5 questions dans l'ordre | Task 3 — `SYSTEM_PROMPT` |
| Déclenchement auto recherche | Task 3 — prompt "IMMÉDIATEMENT" |
| `search_jobs(title, location, experience, skills, contract_type)` | Task 2 — signature exacte |
| `what` = title + skills + experience + contract_type | Task 2 — `what_query` |
| `RESULTS_PER_PAGE = 15` dans config.py | Task 1 |
| `ADZUNA_COUNTRY = "fr"` dans config.py | Task 1 |
| Erreur : aucun résultat → suggestion d'élargir | Task 2 — branche `if not results` |
| Erreur : API injoignable | Task 2 — `except ConnectionError` |
| Erreur : clés manquantes | Task 2 + Task 4 — vérification au démarrage |
| Commentaires pédagogiques sur chaque fichier | Toutes les tâches |
| Docstrings sur chaque fonction | Task 2 — `search_jobs`, Task 4 — `chat_with_agent` |
| `.env.example` | Task 1 |
| `README.md` (prérequis, install, config, lancement) | Task 5 |
