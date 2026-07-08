# applairo/bootstrap.py
# Composition root : le SEUL endroit qui connaît les implémentations concrètes.
#
# On y instancie les adaptateurs et on les injecte dans le cas d'usage via leurs
# ports. Changer de source d'offres, de modèle ou de comité se fait ici, sans
# toucher au domaine ni à l'application.

from applairo.adapters.outbound.adk.offer_evaluator import AdkOfferEvaluator
from applairo.adapters.outbound.adk.profile_extractor import AdkProfileExtractor
from applairo.adapters.outbound.adzuna.adzuna_job_search import AdzunaJobSearch
from applairo.adapters.outbound.cv.document_extractor import DocumentCvExtractor
from applairo.application.job_search_workflow import JobSearchWorkflow
from applairo.config import Settings


def build_workflow(settings: Settings) -> JobSearchWorkflow:
    """Câble tous les adaptateurs et retourne le pipeline de recherche prêt à l'emploi."""
    # Extraction mécanique du texte du CV (PDF / Word / txt).
    cv_extractor = DocumentCvExtractor()

    # Déduction du profil de recherche depuis le CV (LlmAgent, sortie structurée).
    profile_extraction = AdkProfileExtractor(
        model=settings.gemini_model,
        app_name=settings.app_name,
        retry_max=settings.retry_max,
        retry_delay=settings.retry_delay,
        max_output_tokens=settings.max_output_tokens,
    )

    # Recherche d'offres (implémente JobSearchPort). Le workflow l'appelle N fois
    # (fan-out) à partir d'un même profil.
    job_search = AdzunaJobSearch(
        app_id=settings.adzuna_app_id,
        app_key=settings.adzuna_app_key,
        country=settings.adzuna_country,
        results_per_page=settings.results_per_page,
    )

    # Comité d'évaluation multi-agents (RH / Tech lead / Marché).
    offer_evaluation = AdkOfferEvaluator(
        model=settings.gemini_model,
        app_name=settings.app_name,
        retry_max=settings.retry_max,
        retry_delay=settings.retry_delay,
        max_output_tokens=settings.max_output_tokens,
    )

    return JobSearchWorkflow(
        cv_extractor=cv_extractor,
        profile_extraction=profile_extraction,
        job_search=job_search,
        offer_evaluation=offer_evaluation,
        max_search_combos=settings.max_search_combos,
        eval_top_n=settings.eval_top_n,
    )
