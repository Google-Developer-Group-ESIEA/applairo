# domain/ports/profile_extraction.py
# Port sortant : déduire un profil de recherche à partir du texte d'un CV.
#
# Étape LLM : l'implémentation (adapters/outbound/adk/) demande au modèle
# d'inférer intitulés de poste, niveau et localisations depuis le CV.

from typing import Protocol

from applairo.domain.models import SearchProfile


class ProfileExtractionPort(Protocol):
    """Contrat d'un extracteur de profil de recherche depuis un CV."""

    async def extract_profile(self, cv_text: str) -> SearchProfile:
        """Retourne un `SearchProfile` déduit du texte du CV.

        Lève `ProfileExtractionError` si le modèle ne renvoie rien d'exploitable.
        """
        ...
