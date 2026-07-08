# adapters/inbound/http/routes.py
# Routes REST. Fines : elles traduisent HTTP <-> ChatService et rien d'autre.
#
# Le ChatService est injecté à la construction du routeur (pas de singleton
# global), ce qui garde l'adaptateur testable et le câblage explicite.

import logging
import uuid

from fastapi import APIRouter

from applairo.application.chat_service import ChatService

from .schemas import ChatRequest, ChatResponse, StartSessionResponse

logger = logging.getLogger(__name__)


def build_router(chat_service: ChatService) -> APIRouter:
    """Construit le routeur FastAPI branché sur le cas d'usage de conversation."""
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict[str, str]:
        """Sonde de vivacité (utilisée par le healthcheck Docker)."""
        return {"status": "ok"}

    @router.post("/api/sessions", response_model=StartSessionResponse)
    async def create_session() -> StartSessionResponse:
        """Ouvre une session isolée et retourne le message d'accueil de l'agent."""
        session_id = str(uuid.uuid4())
        logger.info("Nouvelle session %s", session_id)
        reply = await chat_service.start_session(session_id)
        return StartSessionResponse(session_id=session_id, reply=reply)

    @router.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """Transmet un message à l'agent et retourne sa réponse."""
        logger.info(
            "Session %s: message reçu (%d car.)",
            request.session_id,
            len(request.message),
        )
        reply = await chat_service.send_message(request.session_id, request.message)
        return ChatResponse(reply=reply)

    return router
