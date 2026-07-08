# domain/models.py
# Entités et objets-valeurs du domaine « recherche d'emploi ».
#
# Ce sont des structures immuables (frozen) et pures : elles ne connaissent
# ni Adzuna, ni ADK, ni HTTP. Les adaptateurs les produisent et les consomment.

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchCriteria:
    """Critères de recherche collectés auprès de l'utilisateur par l'agent."""

    title: str
    location: str
    experience: str
    contract_type: str


@dataclass(frozen=True)
class Job:
    """Une offre d'emploi, indépendante de sa source (Adzuna ou autre)."""

    title: str
    company: str
    location: str
    url: str
    salary_min: int | None = None
    salary_max: int | None = None
