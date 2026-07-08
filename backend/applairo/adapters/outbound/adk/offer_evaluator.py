# adapters/outbound/adk/offer_evaluator.py
# Adaptateur sortant : le comité d'évaluation (implémente OfferEvaluationPort).
#
# Trois membres, trois points de vue, lancés EN PARALLÈLE (asyncio.gather) :
#   - RH        : adéquation culturelle / ton / mots-clés du CV vs l'annonce
#   - Tech lead : crédibilité technique du profil face aux exigences du poste
#   - Marché    : réalisme salaire / séniorité / attractivité de l'offre
#
# Maîtrise du coût (quota Gemini) : chaque membre note TOUTES les offres en UN
# seul appel (batch), pas un appel par offre. Coût = 3 appels par recherche,
# quel que soit le nombre d'offres. Si un membre échoue, on continue avec les
# autres ; on n'échoue que si les trois tombent.

import asyncio
import logging

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from applairo.domain.errors import EvaluationError
from applairo.domain.models import CommitteeScore, Job, ScoredJob, SearchProfile
from applairo.domain.ports.offer_evaluation import MemberDone

from .agent_runner import generation_config, run_agent_once

logger = logging.getLogger(__name__)

# Chaque membre : (identifiant lisible, consigne de son point de vue).
_MEMBERS = [
    (
        "RH",
        "Tu es un recruteur RH. Évalue l'adéquation entre le profil du candidat et "
        "chaque offre du point de vue humain : culture d'entreprise, ton et mots-clés "
        "de l'annonce en regard du profil, cohérence du parcours. Une note haute = "
        "forte compatibilité candidat/entreprise.",
    ),
    (
        "Tech lead",
        "Tu es un tech lead. Confronte les compétences et l'expérience du profil aux "
        "exigences TECHNIQUES de chaque offre. Sois exigeant : signale les écarts de "
        "stack ou de séniorité. Une note haute = le candidat tiendrait le poste "
        "techniquement.",
    ),
    (
        "Marché",
        "Tu es un analyste du marché de l'emploi. Juge le réalisme de chaque offre "
        "pour ce candidat : cohérence salaire/séniorité, attractivité, localisation. "
        "Une note haute = offre réaliste et intéressante pour ce profil.",
    ),
]

_INSTRUCTION_TEMPLATE = """{lens}

On te donne un profil candidat et une liste numérotée d'offres d'emploi.
Pour CHAQUE offre, attribue une note de 0 à 100 selon TON point de vue, et une
justification en une phrase (français, concise).

Réponds uniquement avec le JSON demandé : un objet `evaluations` contenant une
entrée par offre, avec l'`index` exact de l'offre, le `score` et les `notes`.
N'omets aucune offre."""


class _EvalItemDTO(BaseModel):
    index: int
    score: int = Field(ge=0, le=100)
    notes: str = ""


class _EvalDTO(BaseModel):
    evaluations: list[_EvalItemDTO] = Field(default_factory=list)


class AdkOfferEvaluator:
    """Comité d'évaluation d'offres via Gemini (implémente OfferEvaluationPort)."""

    def __init__(
        self,
        model: str,
        app_name: str,
        retry_max: int,
        retry_delay: int,
        max_output_tokens: int,
    ) -> None:
        self._app_name = app_name
        config = generation_config(retry_max, retry_delay, max_output_tokens)
        # Un agent ADK par membre, construit une fois et réutilisé.
        self._agents = [
            (
                member,
                LlmAgent(
                    name=f"committee_{i}",
                    model=model,
                    description=f"Membre du comité d'évaluation : {member}",
                    instruction=_INSTRUCTION_TEMPLATE.format(lens=lens),
                    output_schema=_EvalDTO,
                    generate_content_config=config,
                ),
            )
            for i, (member, lens) in enumerate(_MEMBERS)
        ]

    @property
    def members(self) -> list[str]:
        """Noms des membres, disponibles avant de lancer la délibération."""
        return [member for member, _ in self._agents]

    async def evaluate(
        self,
        profile: SearchProfile,
        jobs: list[Job],
        on_member_done: MemberDone | None = None,
    ) -> list[ScoredJob]:
        if not jobs:
            return []

        prompt = self._build_prompt(profile, jobs)
        logger.info(
            "Comité : évaluation de %d offre(s) par %d membre(s)", len(jobs), len(self._agents)
        )

        # Les trois membres notent en parallèle. Chaque membre renvoie un dict
        # {index offre -> CommitteeScore} ; None si ce membre a échoué. On notifie
        # `on_member_done` dès qu'un membre termine, sans attendre les autres.
        async def run(member: str, agent: LlmAgent) -> dict[int, CommitteeScore] | None:
            scores = await self._run_member(member, agent, prompt, len(jobs))
            if on_member_done is not None:
                on_member_done(member, len(scores) if scores else 0)
            return scores

        results = await asyncio.gather(*(run(member, agent) for member, agent in self._agents))

        member_scores = [r for r in results if r is not None]
        if not member_scores:
            raise EvaluationError("aucun membre du comité n'a pu évaluer les offres")

        return [self._assemble(job, index, member_scores) for index, job in enumerate(jobs)]

    # -- interne ------------------------------------------------------------

    async def _run_member(
        self, member: str, agent: LlmAgent, prompt: str, job_count: int
    ) -> dict[int, CommitteeScore] | None:
        """Fait noter le lot d'offres par un membre. Retourne None si le membre échoue."""
        try:
            raw = await run_agent_once(agent, prompt, self._app_name)
            dto = _EvalDTO.model_validate_json(raw)
        except ValueError as exc:
            logger.warning("Comité (%s) : réponse invalide, membre ignoré : %s", member, exc)
            return None

        scores = {
            item.index: CommitteeScore(member=member, score=item.score, notes=item.notes.strip())
            for item in dto.evaluations
            if 0 <= item.index < job_count
        }
        logger.info("Comité (%s) : %d offre(s) notée(s)", member, len(scores))
        return scores

    @staticmethod
    def _assemble(
        job: Job, index: int, member_scores: list[dict[int, CommitteeScore]]
    ) -> ScoredJob:
        """Regroupe les notes des membres pour une offre et calcule la note globale."""
        scores = tuple(m[index] for m in member_scores if index in m)
        overall = round(sum(s.score for s in scores) / len(scores)) if scores else 0
        return ScoredJob(job=job, scores=scores, overall=overall)

    @staticmethod
    def _build_prompt(profile: SearchProfile, jobs: list[Job]) -> str:
        lines = [
            "## Profil candidat",
            f"Postes visés : {', '.join(profile.titles)}",
            f"Localisations : {', '.join(profile.locations)}",
            f"Niveau : {profile.level or 'non précisé'}",
            f"Contrat : {profile.contract_type or 'non précisé'}",
            "",
            "## Offres à évaluer",
        ]
        for i, job in enumerate(jobs):
            salary = ""
            if job.salary_min:
                salary = f" | salaire ~{job.salary_min}"
                if job.salary_max:
                    salary += f"-{job.salary_max}"
                salary += " €/an"
            # Description tronquée : borne les tokens envoyés au modèle.
            desc = job.description.strip().replace("\n", " ")[:400]
            lines.append(
                f"[{i}] {job.title} - {job.company} - {job.location or 'lieu n/c'}{salary}"
            )
            if desc:
                lines.append(f"    {desc}")
        return "\n".join(lines)
