# adapters/inbound/http/schemas.py
# DTOs HTTP (Pydantic). Frontière de sérialisation : ces schémas appartiennent à
# l'adaptateur web, pas au domaine. Ils traduisent les entités du domaine
# (SearchProfile, ScoredJob...) en JSON stable pour le frontend, et inversement.

from pydantic import BaseModel, Field

from applairo.domain.models import CommitteeScore, Job, ScoredJob, SearchProfile


class SearchProfileDTO(BaseModel):
    """Profil de recherche : produit à l'étape CV, ré-envoyé (éventuellement édité)
    à l'étape recherche. Le pipeline étant sans état, il transite par le frontend."""

    titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    level: str = ""
    contract_type: str = ""

    @classmethod
    def from_domain(cls, profile: SearchProfile) -> "SearchProfileDTO":
        return cls(
            titles=list(profile.titles),
            locations=list(profile.locations),
            level=profile.level,
            contract_type=profile.contract_type,
        )

    def to_domain(self) -> SearchProfile:
        return SearchProfile(
            titles=tuple(t.strip() for t in self.titles if t.strip()),
            locations=tuple(loc.strip() for loc in self.locations if loc.strip()),
            level=self.level.strip(),
            contract_type=self.contract_type.strip(),
        )


class CommitteeScoreDTO(BaseModel):
    """Note d'un membre du comité pour une offre."""

    member: str
    score: int
    notes: str

    @classmethod
    def from_domain(cls, score: CommitteeScore) -> "CommitteeScoreDTO":
        return cls(member=score.member, score=score.score, notes=score.notes)


class JobDTO(BaseModel):
    """Une offre d'emploi (sans les annotations du comité)."""

    title: str
    company: str
    location: str
    url: str
    salary_min: int | None = None
    salary_max: int | None = None

    @classmethod
    def from_domain(cls, job: Job) -> "JobDTO":
        return cls(
            title=job.title,
            company=job.company,
            location=job.location,
            url=job.url,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
        )


class ScoredJobDTO(BaseModel):
    """Une offre annotée par le comité, telle que rendue par le frontend."""

    job: JobDTO
    scores: list[CommitteeScoreDTO]
    overall: int

    @classmethod
    def from_domain(cls, scored: ScoredJob) -> "ScoredJobDTO":
        return cls(
            job=JobDTO.from_domain(scored.job),
            scores=[CommitteeScoreDTO.from_domain(s) for s in scored.scores],
            overall=scored.overall,
        )


class SearchResponse(BaseModel):
    """Réponse de l'étape recherche : les offres évaluées, triées par note globale."""

    jobs: list[ScoredJobDTO]
