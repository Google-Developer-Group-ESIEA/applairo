# applairo/bootstrap.py
# Composition root : le SEUL endroit qui connaît les implémentations concrètes.
#
# On y instancie les adaptateurs et on les injecte dans les services via leurs
# ports. Changer de source d'offres ou de moteur conversationnel se fait ici,
# sans toucher au domaine ni à l'application.

from google.adk.sessions import InMemorySessionService

from applairo.adapters.outbound.adk.adk_conversation import AdkConversation
from applairo.adapters.outbound.adk.agent_factory import build_agent
from applairo.adapters.outbound.adzuna.adzuna_job_search import AdzunaJobSearch
from applairo.application.chat_service import ChatService
from applairo.config import Settings


def build_chat_service(settings: Settings) -> ChatService:
    """Câble Adzuna + ADK et retourne le cas d'usage de conversation prêt à l'emploi."""
    # Adaptateur sortant : recherche d'offres (implémente JobSearchPort).
    job_search = AdzunaJobSearch(
        app_id=settings.adzuna_app_id,
        app_key=settings.adzuna_app_key,
        country=settings.adzuna_country,
        results_per_page=settings.results_per_page,
    )

    # Agent ADK, avec le port de recherche injecté dans son outil.
    agent = build_agent(
        job_search=job_search,
        model=settings.gemini_model,
        retry_max=settings.retry_max,
        retry_delay=settings.retry_delay,
    )

    # Stockage des sessions. InMemory = simple, mais mono-instance (perdu au
    # redémarrage, non partagé entre réplicas). Pour un scaling horizontal,
    # remplacer par DatabaseSessionService - aucun autre changement requis.
    session_service = InMemorySessionService()

    conversation = AdkConversation(
        agent=agent,
        session_service=session_service,
        app_name=settings.app_name,
    )

    return ChatService(conversation=conversation)
