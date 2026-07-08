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

from applairo.domain.models import TokenUsage

logger = logging.getLogger(__name__)


def _to_token_usage(usage_metadata: object) -> TokenUsage:
    """Traduit le `usage_metadata` de genai en TokenUsage du domaine.

    Les tokens de « réflexion » (thinking, propres aux modèles 2.5) sont facturés
    comme de la sortie : on les agrège donc à `output`.
    """
    prompt = getattr(usage_metadata, "prompt_token_count", None) or 0
    candidates = getattr(usage_metadata, "candidates_token_count", None) or 0
    thoughts = getattr(usage_metadata, "thoughts_token_count", None) or 0
    output = candidates + thoughts
    total = getattr(usage_metadata, "total_token_count", None) or (prompt + output)
    return TokenUsage(prompt=prompt, output=output, total=total)


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


async def run_agent_once(
    agent: LlmAgent, prompt: str, app_name: str
) -> tuple[str, TokenUsage | None]:
    """Exécute `agent` sur `prompt` et retourne (texte de la réponse finale, tokens).

    Session éphémère (le pipeline est sans état). Le texte est vide si le modèle
    ne produit aucun contenu final ; `usage` est None si l'API ne renvoie pas de
    métadonnées de consommation. On retient le dernier `usage_metadata` vu : pour
    un appel en un tour, il est porté par l'événement de réponse finale.
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
    usage: TokenUsage | None = None
    async for event in runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=content,
    ):
        metadata = getattr(event, "usage_metadata", None)
        if metadata is not None:
            usage = _to_token_usage(metadata)
        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text or ""

    logger.debug("Agent %s: réponse finale (%d car.), tokens=%s", agent.name, len(text), usage)
    return text, usage
