# adapters/outbound/adzuna/adzuna_job_search.py
# Adaptateur sortant : implémente JobSearchPort en interrogeant l'API Adzuna.
#
# Responsabilité unique : parler HTTP à Adzuna et traduire la réponse JSON en
# entités du domaine (`Job`). Aucune mise en forme pour l'utilisateur ou le LLM
# ici - c'est le rôle de l'adaptateur ADK. En cas d'échec technique, on lève
# `JobSearchError` (le domaine), jamais une exception `requests` brute.
#
# Documentation API : https://developer.adzuna.com/docs/search

import logging

import requests

from applairo.domain.errors import JobSearchError
from applairo.domain.models import Job, SearchCriteria

logger = logging.getLogger(__name__)


class AdzunaJobSearch:
    """Recherche d'offres via l'API Adzuna (implémente JobSearchPort)."""

    _BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str,
        results_per_page: int,
        timeout: int = 10,
    ) -> None:
        self._app_id = app_id
        self._app_key = app_key
        self._country = country
        self._results_per_page = results_per_page
        self._timeout = timeout

    def search(self, criteria: SearchCriteria) -> list[Job]:
        data = self._request(criteria)
        results = data.get("results", [])
        # `count` = total d'offres correspondant côté Adzuna (peut dépasser la
        # page renvoyée). Utile pour distinguer « 0 correspondance » de « page vide ».
        logger.info(
            "Adzuna: %d offre(s) sur cette page (total disponible: %s)",
            len(results),
            data.get("count", "?"),
        )
        return [self._to_job(raw) for raw in results]

    # -- interne ------------------------------------------------------------

    def _request(self, criteria: SearchCriteria) -> dict:
        """Appelle Adzuna et retourne le JSON, ou lève JobSearchError."""
        # Le tier gratuit d'Adzuna n'a pas de filtre `contract_type` dédié : on
        # injecte poste + expérience + contrat dans le champ `what` pour une
        # recherche sémantique (ex: « développeur python senior stage »).
        what_query = f"{criteria.title} {criteria.experience} {criteria.contract_type}".strip()
        url = f"{self._BASE_URL}/{self._country}/search/1"
        params = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "what": what_query,
            "where": criteria.location,
            "results_per_page": self._results_per_page,
        }

        # Requête tracée SANS les secrets (app_id / app_key).
        logger.info(
            "Adzuna GET %s | what=%r where=%r results_per_page=%d",
            url,
            what_query,
            criteria.location,
            self._results_per_page,
        )

        try:
            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            logger.debug("Adzuna: réponse HTTP %d", response.status_code)
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Adzuna injoignable: %s", exc)
            raise JobSearchError(
                "impossible de joindre l'API Adzuna (vérifiez la connexion internet)"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            logger.warning("Adzuna: réponse HTTP %s", status)
            raise JobSearchError(
                f"réponse {status} de l'API Adzuna (vérifiez les clés API)"
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.warning("Adzuna: échec de la requête: %s", exc)
            raise JobSearchError(f"échec de la requête Adzuna : {exc}") from exc

    @staticmethod
    def _to_job(raw: dict) -> Job:
        """Traduit une offre brute Adzuna en entité de domaine `Job`."""
        salary_min = raw.get("salary_min")
        salary_max = raw.get("salary_max")
        return Job(
            title=raw.get("title", "Poste non précisé"),
            company=raw.get("company", {}).get("display_name", "Entreprise non précisée"),
            location=raw.get("location", {}).get("display_name", ""),
            url=raw.get("redirect_url", "#"),
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
        )
