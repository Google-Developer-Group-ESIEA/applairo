# adapters/inbound/http/app.py
# Fabrique de l'application FastAPI.
#
# Pas de CORS : le frontend Next.js appelle le backend côté serveur (BFF /
# proxy), donc les requêtes ne viennent jamais directement du navigateur.

from fastapi import FastAPI

from applairo.bootstrap import build_workflow
from applairo.config import Settings
from applairo.logging_config import configure_logging

from .routes import build_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application HTTP à partir de la configuration."""
    settings = settings or Settings()
    configure_logging(settings.log_level)
    workflow = build_workflow(settings)

    app = FastAPI(title="ApplaiNow API", version="0.2.0")
    app.include_router(build_router(workflow, settings.max_upload_bytes))
    return app
