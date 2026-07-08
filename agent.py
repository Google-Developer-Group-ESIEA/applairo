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
from google.genai import types
from tools.adzuna import search_jobs
from config import GEMINI_MODEL, RETRY_MAX, RETRY_DELAY

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
4. **Type de contrat** — propose les options : CDI / CDD / stage / alternance

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
# - model : modèle Gemini à utiliser (configurable dans config.py)
# - instruction : le prompt système qui guide le comportement de l'agent
# - tools : liste des fonctions Python que l'agent peut appeler
# - generate_content_config : paramètres HTTP dont les retries automatiques
#   sur erreur 429 (quota dépassé) — solution recommandée par la doc ADK :
#   https://adk.dev/agents/models/google-gemini/#error-code-429-resource_exhausted
root_agent = LlmAgent(
    name="job_search_agent",
    model=GEMINI_MODEL,
    description="Agent conversationnel de recherche d'emploi pour le GDG ESIEA",
    instruction=SYSTEM_PROMPT,
    tools=[search_jobs],
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                initial_delay=RETRY_DELAY,
                attempts=RETRY_MAX,
            ),
        ),
    ),
)
