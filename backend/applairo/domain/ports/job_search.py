# domain/ports/job_search.py
# Port sortant : rechercher des offres d'emploi.
#
# Le domaine définit CE dont il a besoin (chercher des offres à partir de
# critères) sans dire COMMENT. L'implémentation (Adzuna, France Travail, un mock
# de test) vit dans adapters/outbound/.

from typing import Protocol

from applairo.domain.models import Job, SearchCriteria


class JobSearchPort(Protocol):
    """Contrat d'un moteur de recherche d'offres d'emploi."""

    def search(self, criteria: SearchCriteria) -> list[Job]:
        """Retourne les offres correspondant aux critères.

        Retourne une liste vide si aucune offre ne correspond.
        Lève `JobSearchError` en cas d'échec technique (réseau, API, auth).
        """
        ...
