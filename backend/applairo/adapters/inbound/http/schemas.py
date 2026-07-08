# adapters/inbound/http/schemas.py
# DTOs HTTP (Pydantic). Frontière de sérialisation : ces schémas appartiennent à
# l'adaptateur web, pas au domaine.

from pydantic import BaseModel, Field


class StartSessionResponse(BaseModel):
    """Réponse à la création d'une session : identifiant + message d'accueil."""

    session_id: str
    reply: str


class ChatRequest(BaseModel):
    """Message utilisateur rattaché à une session existante."""

    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Réponse de l'agent (markdown)."""

    reply: str
