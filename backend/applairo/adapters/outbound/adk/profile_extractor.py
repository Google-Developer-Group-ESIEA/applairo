# adapters/outbound/adk/profile_extractor.py
# Adaptateur sortant : déduit un profil de recherche du CV (implémente
# ProfileExtractionPort) via un LlmAgent ADK en sortie structurée.
#
# `output_schema` force le modèle à répondre en JSON conforme au DTO : pas de
# parsing fragile de texte libre. L'agent n'a donc pas d'outil (contrainte ADK
# quand output_schema est défini), ce qui est voulu : c'est une pure extraction.

import logging

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from applairo.domain.errors import ProfileExtractionError
from applairo.domain.models import SearchProfile, TokenUsage

from .agent_runner import generation_config, run_agent_once

logger = logging.getLogger(__name__)

_INSTRUCTION = """Tu es un expert en recrutement pour le GDG ESIEA.
On te donne le texte brut d'un CV. Déduis-en un profil de recherche d'emploi.

Règles :
- titles : 2 à 5 intitulés de poste PERTINENTS et COURANTS sur le marché, adaptés
  au CV (ex: "Développeur Python", "Data Engineer"). Utilise des intitulés que les
  recruteurs emploient réellement, pas les mots exacts du CV s'ils sont exotiques.
  Chaque intitulé devient une requête de recherche plein texte distincte.
- Variantes enrichies : si le contrat visé est une ALTERNANCE, un APPRENTISSAGE ou
  un STAGE (ces mots figurent souvent tels quels dans les intitulés d'annonces), tu
  PEUX ajouter, EN PLUS de l'intitulé simple, une variante avec ce mot-clé (ex:
  "Développeur Python" ET "Développeur Python alternance"). Émets TOUJOURS l'intitulé
  simple ; n'émets JAMAIS la variante enrichie seule (elle réduirait les résultats).
  N'ajoute PAS de variante pour un CDI/CDD (le mot n'apparaît quasi jamais dans les
  intitulés).
- locations : 1 à 3 localisations plausibles déduites du CV (ville ou région). Si
  le CV n'en mentionne aucune, renvoie ["France"].
- level : un seul mot parmi "junior", "intermédiaire", "senior", selon l'expérience.
- contract_type : le type de contrat visé si déductible (ex: "CDI", "alternance"),
  sinon chaîne vide.

Réponds uniquement avec le JSON demandé, sans commentaire."""


class _ProfileDTO(BaseModel):
    """Schéma de sortie imposé au modèle (frontière ADK, pas le domaine)."""

    titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    level: str = ""
    contract_type: str = ""


class AdkProfileExtractor:
    """Extrait un SearchProfile depuis un CV via Gemini (implémente ProfileExtractionPort)."""

    def __init__(
        self,
        model: str,
        app_name: str,
        retry_max: int,
        retry_delay: int,
        max_output_tokens: int,
    ) -> None:
        self._app_name = app_name
        self._agent = LlmAgent(
            name="profile_extractor",
            model=model,
            description="Déduit un profil de recherche d'emploi à partir d'un CV",
            instruction=_INSTRUCTION,
            output_schema=_ProfileDTO,
            generate_content_config=generation_config(retry_max, retry_delay, max_output_tokens),
        )

    async def extract_profile(self, cv_text: str) -> tuple[SearchProfile, TokenUsage | None]:
        raw, usage = await run_agent_once(self._agent, cv_text, self._app_name)
        try:
            dto = _ProfileDTO.model_validate_json(raw)
        except ValueError as exc:
            logger.warning("Profil : réponse du modèle non parsable : %s", exc)
            raise ProfileExtractionError("le modèle n'a pas renvoyé un profil valide") from exc

        # Nettoyage : on écarte les entrées vides que le modèle pourrait glisser.
        titles = tuple(t.strip() for t in dto.titles if t.strip())
        locations = tuple(loc.strip() for loc in dto.locations if loc.strip()) or ("France",)
        if not titles:
            raise ProfileExtractionError("aucun intitulé de poste n'a pu être déduit du CV")

        profile = SearchProfile(
            titles=titles,
            locations=locations,
            level=dto.level.strip(),
            contract_type=dto.contract_type.strip(),
        )
        logger.info(
            "Profil déduit : titles=%s locations=%s level=%r (tokens=%s)",
            list(profile.titles),
            list(profile.locations),
            profile.level,
            usage.total if usage else "?",
        )
        return profile, usage
