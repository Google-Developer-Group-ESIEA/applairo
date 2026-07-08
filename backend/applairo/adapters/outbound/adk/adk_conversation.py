# adapters/outbound/adk/adk_conversation.py
# Adaptateur sortant : implémente ConversationPort avec le Runner ADK.
#
# Le `Runner` (agent + service de session) est construit UNE fois, à la création
# de l'adaptateur, puis réutilisé à chaque message - pas de reconstruction par
# requête.
#
# Le service de session est injecté (BaseSessionService). En V1 c'est un
# InMemorySessionService (voir bootstrap.py) ; pour un passage à l'échelle
# horizontal, il suffit d'injecter un DatabaseSessionService sans rien changer
# ici - c'est tout l'intérêt de l'inversion de dépendance.

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.genai.types import Content, Part


class AdkConversation:
    """Moteur conversationnel basé sur Google ADK (implémente ConversationPort)."""

    _WELCOME_TRIGGER = "Bonjour !"

    def __init__(
        self,
        agent: LlmAgent,
        session_service: BaseSessionService,
        app_name: str,
    ) -> None:
        self._session_service = session_service
        self._app_name = app_name
        self._runner = Runner(
            agent=agent,
            app_name=app_name,
            session_service=session_service,
        )

    async def start_session(self, session_id: str) -> str:
        """Crée une session ADK isolée et retourne le message d'accueil."""
        await self._session_service.create_session(
            app_name=self._app_name,
            user_id=session_id,
            session_id=session_id,
        )
        return await self.send_message(session_id, self._WELCOME_TRIGGER)

    async def send_message(self, session_id: str, message: str) -> str:
        """Transmet un message à l'agent et retourne sa réponse finale.

        Les retries sur erreur 429 (quota Gemini) sont gérés nativement par
        l'agent via son generate_content_config (voir agent_factory.py).
        """
        user_content = Content(role="user", parts=[Part(text=message)])

        response_text = ""
        async for event in self._runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=user_content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text or ""

        return response_text
