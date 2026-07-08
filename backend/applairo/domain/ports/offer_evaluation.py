# domain/ports/offer_evaluation.py
# Port sortant : faire évaluer des offres par le comité.
#
# Étape LLM multi-agents : chaque membre du comité (RH, Tech lead, Marché) note
# les offres selon son point de vue. L'implémentation (adapters/outbound/adk/)
# lance les membres en parallèle et fusionne leurs notes.

from typing import Protocol

from applairo.domain.models import Job, ScoredJob, SearchProfile


class OfferEvaluationPort(Protocol):
    """Contrat d'un comité d'évaluation d'offres d'emploi."""

    async def evaluate(self, profile: SearchProfile, jobs: list[Job]) -> list[ScoredJob]:
        """Retourne les offres annotées par le comité, dans le même ordre.

        Lève `EvaluationError` en cas d'échec technique du comité.
        """
        ...
