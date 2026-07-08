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
    # Plafond de jetons produits par agent et par run (comité, extraction profil).
    # Chaque agent n'est appelé qu'une fois par recherche : borne le coût LLM d'un
    # agent sur un run. Généreux par défaut pour ne pas tronquer le JSON du comité
    # (jusqu'à eval_top_n évaluations).
    max_output_tokens: int = 8192

    # -- Pipeline V2 (entonnoir) -------------------------------------------
    max_search_combos: int = 10  # nb max de requêtes (intitulé x localisation) en fan-out
    eval_top_n: int = 12  # nb max d'offres soumises au comité (borne le coût LLM)
    max_upload_bytes: int = 5 * 1024 * 1024  # taille max d'un CV uploadé (5 Mo)

    # -- Divers -------------------------------------------------------------
    app_name: str = "job_search_agent"
    log_level: str = "INFO"  # DEBUG pour tracer les URLs/paramètres complets
