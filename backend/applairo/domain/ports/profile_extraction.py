# domain/ports/profile_extraction.py
# Port sortant : déduire un profil de recherche à partir du texte d'un CV.
#
# Étape LLM : l'implémentation (adapters/outbound/adk/) demande au modèle
# d'inférer intitulés de poste, niveau et localisations depuis le CV.

from typing import Protocol

from applairo.domain.models import SearchProfile, TokenUsage


class ProfileExtractionPort(Protocol):
    """Contrat d'un extracteur de profil de recherche depuis un CV."""

    async def extract_profile(self, cv_text: str) -> tuple[SearchProfile, TokenUsage | None]:
        """Retourne le `SearchProfile` déduit du CV et la consommation de tokens.

        `TokenUsage` est None si la source ne renvoie pas de métadonnées de
        consommation. Lève `ProfileExtractionError` si le modèle ne renvoie rien
        d'exploitable.
        """
        ...
