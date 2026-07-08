# domain/models.py
# Entités et objets-valeurs du domaine « recherche d'emploi ».
#
# Ce sont des structures immuables (frozen) et pures : elles ne connaissent
# ni Adzuna, ni ADK, ni HTTP. Les adaptateurs les produisent et les consomment.
#
# Les collections sont des tuples (et non des listes) pour rester réellement
# immuables : `frozen=True` empêche de réassigner un champ, pas de muter une
# liste qu'il contiendrait.

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchCriteria:
    """Critères d'une requête unitaire envoyée au moteur de recherche d'offres.

    Une recherche V2 en produit plusieurs (fan-out) à partir d'un SearchProfile.
    """

    title: str
    location: str
    experience: str
    contract_type: str


@dataclass(frozen=True)
class SearchProfile:
    """Profil de recherche déduit du CV, puis ajustable par l'utilisateur.

    Plusieurs intitulés et plusieurs localisations sont possibles : la recherche
    les combine (fan-out) pour maximiser le nombre d'offres trouvées.
    """

    titles: tuple[str, ...]
    locations: tuple[str, ...]
    level: str = ""
    contract_type: str = ""


@dataclass(frozen=True)
class Job:
    """Une offre d'emploi, indépendante de sa source (Adzuna ou autre)."""

    title: str
    company: str
    location: str
    url: str
    description: str = ""
    salary_min: int | None = None
    salary_max: int | None = None


@dataclass(frozen=True)
class TokenUsage:
    """Consommation de tokens d'un appel au modèle (télémétrie de coût).

    Valeur pure (des entiers, aucune dépendance technique) : la maîtrise du coût
    LLM est une préoccupation centrale de cette app (voir l'entonnoir), donc les
    tokens font partie de son vocabulaire. `output` agrège les tokens de sortie
    ET de « réflexion » (thinking), tous deux facturés comme de la sortie.
    """

    prompt: int
    output: int
    total: int


@dataclass(frozen=True)
class CommitteeScore:
    """Note et commentaire d'un membre du comité d'évaluation pour une offre.

    `member` identifie le point de vue (ex: "RH", "Tech lead", "Marché").
    `score` est sur 100 ; `notes` justifie la note en une ou deux phrases.
    """

    member: str
    score: int
    notes: str


@dataclass(frozen=True)
class ScoredJob:
    """Une offre annotée par le comité (compose `Job`, ne l'étend pas).

    `overall` est la synthèse des notes des membres (moyenne), calculée par la
    couche application pour rester une donnée du domaine, pas un détail d'affichage.
    """

    job: Job
    scores: tuple[CommitteeScore, ...]
    overall: int
