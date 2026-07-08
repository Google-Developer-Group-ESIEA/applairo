# adapters/outbound/adk/agent_runner.py
# Utilitaire interne : exécuter un LlmAgent ADK sur un seul message.
#
# Le pipeline V2 est SANS ÉTAT (pas de conversation) : chaque appel au modèle est
# un aller-retour isolé. On crée donc une session ADK éphémère par appel, on lance
# le Runner, et on retourne le texte de la réponse finale. Les agents concernés
# utilisent `output_schema`, donc ce texte est du JSON directement validable.

import logging
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)


def generation_config(
    retry_max: int, retry_delay: int, max_output_tokens: int
) -> types.GenerateContentConfig:
    """Config de génération d'un agent, pour UN appel (= un agent dans un run).

    - retries automatiques sur erreur 429 (quota Gemini) ;
    - `max_output_tokens` : plafond de jetons produits PAR AGENT et PAR RUN. Chaque
      agent (extracteur de profil, membres du comité) est appelé une seule fois par
      recherche : ce plafond borne donc son budget de jetons pour le run et protège
      du coût d'une réponse qui s'emballe.
    """
    return types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                initial_delay=retry_delay,
                attempts=retry_max,
            ),
        ),
    )


async def run_agent_once(agent: LlmAgent, prompt: str, app_name: str) -> str:
    """Exécute `agent` sur `prompt` et retourne le texte de sa réponse finale.

    Session éphémère (le pipeline est sans état). Retourne une chaîne vide si le
    modèle ne produit aucun contenu final.
    """
    session_service = InMemorySessionService()
    session_id = uuid.uuid4().hex
    await session_service.create_session(
        app_name=app_name,
        user_id=session_id,
        session_id=session_id,
    )
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    content = Content(role="user", parts=[Part(text=prompt)])

    text = ""
    async for event in runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text or ""

    logger.debug("Agent %s: réponse finale (%d car.)", agent.name, len(text))
    return text
