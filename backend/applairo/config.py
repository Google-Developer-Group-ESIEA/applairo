# applairo/config.py
# Configuration typée, chargée depuis l'environnement (12-factor).
#
# pydantic-settings valide les variables au démarrage : une clé Adzuna manquante
# lève une erreur explicite plutôt qu'un échec obscur à la première requête.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs lus depuis les variables d'environnement."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # -- Adzuna (obligatoire) ----------------------------------------------
    adzuna_app_id: str
    adzuna_app_key: str
    adzuna_country: str = "fr"

    # -- Agent / Gemini -----------------------------------------------------
    gemini_model: str = "gemini-2.5-flash"
    results_per_page: int = 15
    retry_max: int = 3  # tentatives sur erreur 429
    retry_delay: int = 5  # délai initial (s), doublé à chaque essai

    # -- Divers -------------------------------------------------------------
    app_name: str = "job_search_agent"
    log_level: str = "INFO"  # DEBUG pour tracer les URLs/paramètres complets
