# adapters/inbound/http/routes.py
# Routes REST du pipeline V2. Fines : elles traduisent HTTP <-> JobSearchWorkflow
# et les erreurs du domaine en codes HTTP, rien d'autre.
#
# Deux endpoints, tous deux STATELESS :
#   POST /api/cv     : CV (multipart) -> profil de recherche déduit
#   POST /api/search : profil (édité) -> offres évaluées par le comité
#
# Le workflow est injecté à la construction du routeur (pas de singleton global).

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from applairo.application.job_search_workflow import JobSearchWorkflow
from applairo.domain.errors import (
    CvExtractionError,
    EvaluationError,
    ProfileExtractionError,
)

from .schemas import ScoredJobDTO, SearchProfileDTO, SearchResponse

logger = logging.getLogger(__name__)


def build_router(workflow: JobSearchWorkflow, max_upload_bytes: int) -> APIRouter:
    """Construit le routeur FastAPI branché sur le pipeline de recherche."""
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict[str, str]:
        """Sonde de vivacité (utilisée par le healthcheck Docker)."""
        return {"status": "ok"}

    @router.post("/api/cv", response_model=SearchProfileDTO)
    async def analyze_cv(file: UploadFile = File(...)) -> SearchProfileDTO:
        """Étapes 1-3 : reçoit un CV et retourne le profil de recherche déduit."""
        content = await file.read()
        logger.info("CV reçu : %r (%d octets)", file.filename, len(content))
        if not content:
            raise HTTPException(status_code=400, detail="fichier vide")
        if len(content) > max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"fichier trop volumineux (max {max_upload_bytes // (1024 * 1024)} Mo)",
            )
        try:
            profile = await workflow.profile_from_cv(content, file.filename or "cv")
        except CvExtractionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ProfileExtractionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return SearchProfileDTO.from_domain(profile)

    @router.post("/api/search", response_model=SearchResponse)
    async def search(profile_dto: SearchProfileDTO) -> SearchResponse:
        """Étape 5 : reçoit un profil (édité) et retourne les offres évaluées."""
        profile = profile_dto.to_domain()
        if not profile.titles:
            raise HTTPException(status_code=400, detail="au moins un intitulé de poste est requis")
        logger.info(
            "Recherche demandée : titles=%s locations=%s",
            list(profile.titles),
            list(profile.locations),
        )
        try:
            scored = await workflow.search(profile)
        except EvaluationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        # Tri par note globale décroissante : les meilleures offres en tête.
        scored.sort(key=lambda s: s.overall, reverse=True)
        logger.info("Recherche : %d offre(s) évaluée(s) renvoyée(s)", len(scored))
        return SearchResponse(jobs=[ScoredJobDTO.from_domain(s) for s in scored])

    return router
