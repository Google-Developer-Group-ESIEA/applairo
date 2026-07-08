# application/progress.py
# Événements d'avancement émis par le pipeline pendant une recherche (étape 5).
#
# Le workflow `search_stream` produit un flux de ces événements pour donner à voir
# le travail des agents EN TEMPS RÉEL : requêtes générées, offres qui remontent,
# puis le comité qui délibère membre par membre. Ce sont des types APPLICATIFS
# (pas du domaine) : ils décrivent le déroulé d'un cas d'usage, pas une entité
# métier. L'adaptateur HTTP les traduit en lignes NDJSON ; le workflow, lui,
# ignore tout du transport.

from dataclasses import dataclass, field

from applairo.domain.models import ScoredJob


@dataclass(frozen=True)
class Progress:
    """Étape intermédiaire. `data` ne contient que des primitives JSON-safe."""

    stage: str
    data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SearchComplete:
    """Événement terminal : les offres évaluées et triées."""

    jobs: list[ScoredJob]
