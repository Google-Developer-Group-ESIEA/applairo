# adapters/inbound/http/app.py
# Fabrique de l'application FastAPI.
#
# Pas de CORS : le frontend Next.js appelle le backend côté serveur (BFF /
# proxy), donc les requêtes ne viennent jamais directement du navigateur.

from fastapi import FastAPI

from applairo.bootstrap import build_chat_service
from applairo.config import Settings

from .routes import build_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application HTTP à partir de la configuration."""
    settings = settings or Settings()
    chat_service = build_chat_service(settings)

    app = FastAPI(title="Applairo API", version="0.1.0")
    app.include_router(build_router(chat_service))
    return app
