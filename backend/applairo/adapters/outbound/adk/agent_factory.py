# adapters/outbound/adk/agent_factory.py
# Construit l'agent ADK et connecte son outil `search_jobs` au JobSearchPort.
#
# Point clé hexagonal : l'outil exposé au LLM est une fermeture (closure) qui
# délègue au port. L'agent ne connaît donc pas Adzuna - seulement l'abstraction.
# La mise en forme des offres en markdown est ici (présentation destinée au LLM),
# volontairement séparée de l'adaptateur Adzuna qui, lui, ne renvoie que des `Job`.

import logging

from google.adk.agents import LlmAgent
from google.genai import types

from applairo.domain.errors import JobSearchError
from applairo.domain.models import Job, SearchCriteria
from applairo.domain.ports.job_search import JobSearchPort

logger = logging.getLogger(__name__)

# Le prompt système définit le comportement et la personnalité de l'agent.
# Il guide le LLM pour poser les questions dans le bon ordre et déclencher la
# recherche au bon moment.
SYSTEM_PROMPT = """Tu es JobBot, un assistant de recherche d'emploi créé pour le GDG ESIEA.
Tu aides les utilisateurs à trouver des offres d'emploi adaptées à leur profil.

## Ta mission

Collecter 4 informations sur l'utilisateur, puis lancer automatiquement une recherche d'emploi.

## Protocole de collecte (OBLIGATOIRE)

Pose ces questions UNE PAR UNE, dans cet ordre exact. N'en pose JAMAIS deux en même temps.

1. **Poste recherché** - demande l'intitulé du poste (ex: Développeur Python, Data Scientist, Chef de projet)
2. **Localisation** - demande la ville ou la région souhaitée
3. **Niveau d'expérience** - propose clairement les 3 options : junior / intermédiaire / senior
4. **Type de contrat** - propose les options : CDI / CDD / stage / alternance

## Après la collecte

Dès que tu as les 4 informations, appelle IMMÉDIATEMENT l'outil search_jobs sans attendre de confirmation.
Annonce que tu lances la recherche, puis présente les résultats de façon enthousiaste.

## Ton style

- Accueille chaleureusement l'utilisateur avec une courte présentation (2 phrases max)
- Sois concis et professionnel
- Si une réponse est ambiguë, demande une clarification avant de passer à la question suivante
- Après les résultats, propose de relancer une recherche avec des critères différents
"""


def build_agent(
    job_search: JobSearchPort,
    model: str,
    retry_max: int,
    retry_delay: int,
) -> LlmAgent:
    """Assemble le LlmAgent ADK en injectant le port de recherche d'offres."""

    def search_jobs(
        title: str,
        location: str,
        experience: str,
        contract_type: str,
    ) -> str:
        """Recherche des offres d'emploi selon le profil de l'utilisateur.

        Appelée automatiquement par l'agent une fois les 4 informations collectées.

        Args:
            title: Intitulé du poste recherché (ex: "Développeur Python")
            location: Ville ou région souhaitée (ex: "Paris", "Lyon")
            experience: Niveau d'expérience (ex: "junior", "senior")
            contract_type: Type de contrat souhaité (ex: "CDI", "stage")

        Returns:
            Une liste d'offres formatée en markdown, ou un message d'erreur.
        """
        criteria = SearchCriteria(
            title=title,
            location=location,
            experience=experience,
            contract_type=contract_type,
        )
        # Trace ce que le modèle a réellement extrait et transmis à l'outil.
        logger.info(
            "Outil search_jobs appelé | title=%r location=%r experience=%r contract_type=%r",
            title,
            location,
            experience,
            contract_type,
        )
        try:
            jobs = job_search.search(criteria)
        except JobSearchError as exc:
            logger.warning("search_jobs: échec de la recherche: %s", exc)
            return f"Erreur lors de la recherche : {exc}."
        logger.info("search_jobs: %d offre(s) renvoyée(s) au modèle", len(jobs))
        return _format_jobs(jobs, criteria)

    # generate_content_config : retries automatiques sur erreur 429 (quota
    # dépassé), solution recommandée par la doc ADK.
    # https://adk.dev/agents/models/google-gemini/#error-code-429-resource_exhausted
    return LlmAgent(
        name="job_search_agent",
        model=model,
        description="Agent conversationnel de recherche d'emploi pour le GDG ESIEA",
        instruction=SYSTEM_PROMPT,
        tools=[search_jobs],
        generate_content_config=types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=retry_delay,
                    attempts=retry_max,
                ),
            ),
        ),
    )


def _format_jobs(jobs: list[Job], criteria: SearchCriteria) -> str:
    """Met en forme les offres en markdown, à destination du modèle de langage."""
    if not jobs:
        return (
            f"Aucune offre trouvée pour « {criteria.title} » à « {criteria.location} ».\n\n"
            "Suggestions pour élargir la recherche :\n"
            "- Essayer une ville plus grande ou une région\n"
            "- Simplifier l'intitulé du poste"
        )

    lines = [
        f"**{len(jobs)} offres trouvées pour « {criteria.title} » à « {criteria.location} »**",
        "",
        "---",
        "",
    ]
    for i, job in enumerate(jobs, 1):
        lines.append(f"### {i}. {job.title}")
        lines.append(f"**{job.company}**")
        if job.location:
            lines.append(job.location)
        salary = _format_salary(job)
        if salary:
            lines.append(salary)
        lines.append(f"[Voir l'offre]({job.url})")
        lines.append("")
    return "\n".join(lines)


def _format_salary(job: Job) -> str:
    """Formate la fourchette de salaire si disponible."""
    if job.salary_min and job.salary_max:
        return f"{job.salary_min:,} - {job.salary_max:,} €/an"
    if job.salary_min:
        return f"À partir de {job.salary_min:,} €/an"
    return ""
