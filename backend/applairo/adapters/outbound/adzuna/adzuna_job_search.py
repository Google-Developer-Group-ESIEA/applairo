# adapters/outbound/adzuna/adzuna_job_search.py
# Adaptateur sortant : implémente JobSearchPort en interrogeant l'API Adzuna.
#
# Responsabilité unique : parler HTTP à Adzuna et traduire la réponse JSON en
# entités du domaine (`Job`). Aucune mise en forme pour l'utilisateur ou le LLM
# ici - c'est le rôle de l'adaptateur ADK. En cas d'échec technique, on lève
# `JobSearchError` (le domaine), jamais une exception `requests` brute.
#
# Documentation API : https://developer.adzuna.com/docs/search

import requests

from applairo.domain.errors import JobSearchError
from applairo.domain.models import Job, SearchCriteria


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
        return [self._to_job(raw) for raw in data.get("results", [])]

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

        try:
            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            raise JobSearchError(
                "impossible de joindre l'API Adzuna (vérifiez la connexion internet)"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            raise JobSearchError(
                f"réponse {status} de l'API Adzuna (vérifiez les clés API)"
            ) from exc
        except requests.exceptions.RequestException as exc:
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
