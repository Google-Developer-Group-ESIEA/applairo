# domain/ports/offer_evaluation.py
# Port sortant : faire évaluer des offres par le comité.
#
# Étape LLM multi-agents : chaque membre du comité (RH, Tech lead, Marché) note
# les offres selon son point de vue. L'implémentation (adapters/outbound/adk/)
# lance les membres en parallèle et fusionne leurs notes.

from typing import Callable, Protocol

from applairo.domain.models import Job, ScoredJob, SearchProfile

# Appelé dès qu'un membre a fini de noter : (nom du membre, nombre d'offres notées).
# Sert à retransmettre l'avancement du comité en temps réel (voir search_stream).
MemberDone = Callable[[str, int], None]


class OfferEvaluationPort(Protocol):
    """Contrat d'un comité d'évaluation d'offres d'emploi."""

    @property
    def members(self) -> list[str]:
        """Noms des membres du comité, connus avant même de lancer l'évaluation."""
        ...

    async def evaluate(
        self,
        profile: SearchProfile,
        jobs: list[Job],
        on_member_done: MemberDone | None = None,
    ) -> list[ScoredJob]:
        """Retourne les offres annotées par le comité, dans le même ordre.

        Si `on_member_done` est fourni, il est appelé au fil de l'eau dès qu'un
        membre a terminé (pour un affichage d'avancement). Lève `EvaluationError`
        en cas d'échec technique du comité.
        """
        ...
