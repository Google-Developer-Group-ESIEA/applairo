# application/job_search_workflow.py
# Cas d'usage central de la V2 : le pipeline de recherche d'emploi.
#
# Orchestre les ports (jamais les technologies) selon un ENTONNOIR qui maîtrise
# le coût LLM :
#
#   CV (octets) --[CvExtractorPort, mécanique]--> texte
#   texte -------[ProfileExtractionPort, 1 appel LLM]--> SearchProfile
#   profil ------[JobSearchPort x N, fan-out, SANS LLM]--> offres brutes
#   dédoublonnage (URL) puis coupe aux N meilleures (heuristique, SANS LLM)
#   top-N -------[OfferEvaluationPort, comité, 3 appels LLM]--> ScoredJob[]
#
# Le pipeline est SANS ÉTAT : le frontend garde le profil (issu de l'étape CV) et
# le renvoie tel quel à l'étape recherche. Aucun stockage de session côté backend.

import asyncio
import logging

from applairo.domain.models import Job, ScoredJob, SearchCriteria, SearchProfile
from applairo.domain.ports.cv_extractor import CvExtractorPort
from applairo.domain.ports.job_search import JobSearchPort
from applairo.domain.ports.offer_evaluation import OfferEvaluationPort
from applairo.domain.ports.profile_extraction import ProfileExtractionPort

logger = logging.getLogger(__name__)


class JobSearchWorkflow:
    """Pipeline CV -> profil -> recherche multi-requêtes -> évaluation par le comité."""

    def __init__(
        self,
        cv_extractor: CvExtractorPort,
        profile_extraction: ProfileExtractionPort,
        job_search: JobSearchPort,
        offer_evaluation: OfferEvaluationPort,
        max_search_combos: int,
        eval_top_n: int,
    ) -> None:
        self._cv_extractor = cv_extractor
        self._profile_extraction = profile_extraction
        self._job_search = job_search
        self._offer_evaluation = offer_evaluation
        self._max_search_combos = max_search_combos
        self._eval_top_n = eval_top_n

    async def profile_from_cv(self, content: bytes, filename: str) -> SearchProfile:
        """Étapes 1-3 : extrait le texte du CV puis en déduit un profil de recherche."""
        text = self._cv_extractor.extract_text(content, filename)
        return await self._profile_extraction.extract_profile(text)

    async def search(self, profile: SearchProfile) -> list[ScoredJob]:
        """Étape 5 : fan-out de recherche, dédoublonnage, coupe, évaluation comité."""
        jobs = await self._fan_out(profile)
        unique = self._dedupe(jobs)
        top = unique[: self._eval_top_n]
        if len(unique) > len(top):
            logger.info(
                "Recherche : %d offres uniques, %d envoyées au comité (coupe à %d)",
                len(unique),
                len(top),
                self._eval_top_n,
            )
        return await self._offer_evaluation.evaluate(profile, top)

    # -- interne ------------------------------------------------------------

    async def _fan_out(self, profile: SearchProfile) -> list[Job]:
        """Lance en parallèle une recherche par combinaison (intitulé x localisation)."""
        criteria = self._build_criteria(profile)
        logger.info("Recherche : fan-out sur %d requête(s)", len(criteria))
        # `job_search.search` est synchrone (requests) : on le pousse dans un thread
        # pour lancer toutes les requêtes Adzuna en parallèle sans bloquer l'event loop.
        results = await asyncio.gather(*(asyncio.to_thread(self._safe_search, c) for c in criteria))
        return [job for batch in results for job in batch]

    def _build_criteria(self, profile: SearchProfile) -> list[SearchCriteria]:
        """Produit les couples (intitulé, localisation), plafonnés à max_search_combos."""
        combos: list[SearchCriteria] = []
        for title in profile.titles:
            for location in profile.locations:
                combos.append(
                    SearchCriteria(
                        title=title,
                        location=location,
                        experience=profile.level,
                        contract_type=profile.contract_type,
                    )
                )
        if len(combos) > self._max_search_combos:
            logger.info(
                "Recherche : %d combinaisons possibles, plafonnées à %d",
                len(combos),
                self._max_search_combos,
            )
        return combos[: self._max_search_combos]

    def _safe_search(self, criteria: SearchCriteria) -> list[Job]:
        """Recherche unitaire tolérante : une requête en échec ne casse pas le fan-out."""
        try:
            return self._job_search.search(criteria)
        except Exception as exc:  # JobSearchError ou imprévu : on isole la panne
            logger.warning("Recherche : requête %r échouée, ignorée : %s", criteria.title, exc)
            return []

    @staticmethod
    def _dedupe(jobs: list[Job]) -> list[Job]:
        """Dédoublonne par URL en conservant l'ordre (donc la pertinence Adzuna)."""
        seen: set[str] = set()
        unique: list[Job] = []
        for job in jobs:
            if job.url in seen:
                continue
            seen.add(job.url)
            unique.append(job)
        return unique
