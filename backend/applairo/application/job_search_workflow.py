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
from collections.abc import AsyncIterator

from applairo.application.progress import Progress, SearchComplete
from applairo.domain.errors import EvaluationError
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
        """Étape 5 : fan-out de recherche, entrelacement, dédoublonnage, coupe, comité."""
        batches = await self._fan_out(profile)
        merged = self._interleave(batches)
        unique = self._dedupe(merged)
        top = unique[: self._eval_top_n]
        if len(unique) > len(top):
            logger.info(
                "Recherche : %d offres uniques, %d envoyées au comité (coupe à %d)",
                len(unique),
                len(top),
                self._eval_top_n,
            )
        return await self._offer_evaluation.evaluate(profile, top)

    async def search_stream(
        self, profile: SearchProfile
    ) -> AsyncIterator[Progress | SearchComplete]:
        """Étape 5 en flux : mêmes étapes que `search`, mais chaque avancement est
        émis au fil de l'eau pour donner à voir le travail des agents.

        Le vrai temps de calcul vit dans le comité (3 appels LLM parallèles) : on
        y émet un événement dès qu'un membre a fini, sans attendre les autres. Le
        fan-out et le dédoublonnage sont quasi instantanés : on les montre tels
        quels, sans latence artificielle.

        On produit le travail dans une tâche de fond qui pousse les événements dans
        une file ; le générateur draine cette file. C'est ce qui permet d'émettre
        un membre du comité DÈS qu'il termine, alors que les trois tournent en
        parallèle.
        """
        queue: asyncio.Queue[Progress | SearchComplete | None] = asyncio.Queue()

        async def produce() -> None:
            try:
                criteria = self._build_criteria(profile)
                await queue.put(
                    Progress(
                        "queries",
                        {"queries": [{"title": c.title, "location": c.location} for c in criteria]},
                    )
                )

                # Fan-out réel : les requêtes Adzuna partent en parallèle, on émet
                # un `query_done` par requête (dans l'ordre) dès que le lot revient.
                # Le RYTHME d'affichage est géré côté frontend (choix produit), pas
                # ici : le flux reste à sa vitesse réelle.
                batches = await self._fan_out(profile)
                for c, batch in zip(criteria, batches):
                    await queue.put(
                        Progress(
                            "query_done",
                            {"title": c.title, "location": c.location, "count": len(batch)},
                        )
                    )

                merged = self._interleave(batches)
                unique = self._dedupe(merged)
                top = unique[: self._eval_top_n]
                await queue.put(
                    Progress(
                        "merged",
                        {"found": len(merged), "unique": len(unique), "kept": len(top)},
                    )
                )

                if top:
                    await queue.put(
                        Progress(
                            "committee_start",
                            {"members": self._offer_evaluation.members, "offers": len(top)},
                        )
                    )

                    def on_member_done(member: str, count: int) -> None:
                        queue.put_nowait(
                            Progress("member_done", {"member": member, "count": count})
                        )

                    scored = await self._offer_evaluation.evaluate(profile, top, on_member_done)
                else:
                    scored = []

                scored.sort(key=lambda s: s.overall, reverse=True)
                await queue.put(SearchComplete(jobs=scored))
            except EvaluationError as exc:
                await queue.put(Progress("error", {"detail": str(exc)}))
            except Exception:
                logger.exception("Recherche (flux) : échec inattendu")
                await queue.put(Progress("error", {"detail": "recherche impossible"}))
            finally:
                await queue.put(None)  # sentinelle de fin

        task = asyncio.create_task(produce())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            await task

    # -- interne ------------------------------------------------------------

    async def _fan_out(self, profile: SearchProfile) -> list[list[Job]]:
        """Lance en parallèle une recherche par combinaison (intitulé x localisation).

        Retourne les résultats groupés PAR requête (pas aplatis) pour permettre un
        entrelacement équitable ensuite.
        """
        criteria = self._build_criteria(profile)
        logger.info("Recherche : fan-out sur %d requête(s)", len(criteria))
        # `job_search.search` est synchrone (requests) : on le pousse dans un thread
        # pour lancer toutes les requêtes Adzuna en parallèle sans bloquer l'event loop.
        return await asyncio.gather(*(asyncio.to_thread(self._safe_search, c) for c in criteria))

    @staticmethod
    def _interleave(batches: list[list[Job]]) -> list[Job]:
        """Fusionne les résultats en round-robin : rang 1 de chaque requête, puis
        rang 2, etc.

        Sans cela, la simple concaténation ferait que la 1re requête sature le
        top-N (Adzuna ne renvoie que `results_per_page` offres, déjà triées) et que
        les requêtes suivantes - notamment les variantes enrichies d'un mot-clé -
        seraient coupées avant même d'atteindre le comité. L'entrelacement garantit
        que chaque requête contribue équitablement aux offres retenues.
        """
        merged: list[Job] = []
        if not batches:
            return merged
        for rank in range(max(len(batch) for batch in batches)):
            for batch in batches:
                if rank < len(batch):
                    merged.append(batch[rank])
        return merged

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
