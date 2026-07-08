# domain/ports/conversation.py
# Port sortant : mener une conversation avec l'utilisateur.
#
# Abstrait le moteur conversationnel. L'implémentation actuelle s'appuie sur
# Google ADK (adapters/outbound/adk/), mais l'application n'en sait rien : elle
# ne manipule que ce port.

from typing import Protocol


class ConversationPort(Protocol):
    """Contrat d'un moteur de conversation à mémoire de session."""

    async def start_session(self, session_id: str) -> str:
        """Ouvre une nouvelle session et retourne le message d'accueil de l'agent."""
        ...

    async def send_message(self, session_id: str, message: str) -> str:
        """Transmet un message utilisateur et retourne la réponse de l'agent."""
        ...
