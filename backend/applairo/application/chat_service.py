# application/chat_service.py
# Cas d'usage de conversation : frontière applicative entre l'adaptateur HTTP
# entrant et le port de conversation.
#
# Volontairement mince. L'orchestration de l'agent (boucle LLM + appels d'outils)
# appartient au moteur conversationnel (ADK), pas ici : ce service se contente
# d'exposer les opérations métier au monde extérieur en dépendant d'une
# abstraction (ConversationPort), jamais d'ADK directement.

from applairo.domain.ports.conversation import ConversationPort


class ChatService:
    """Orchestre les échanges entre l'utilisateur et le moteur conversationnel."""

    def __init__(self, conversation: ConversationPort) -> None:
        self._conversation = conversation

    async def start_session(self, session_id: str) -> str:
        """Ouvre une session et retourne le message d'accueil de l'agent."""
        return await self._conversation.start_session(session_id)

    async def send_message(self, session_id: str, message: str) -> str:
        """Transmet un message utilisateur et retourne la réponse de l'agent."""
        return await self._conversation.send_message(session_id, message)
