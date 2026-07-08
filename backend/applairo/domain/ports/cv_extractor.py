# domain/ports/cv_extractor.py
# Port sortant : extraire le texte brut d'un CV.
#
# Étape mécanique (pas de LLM) : PDF, Word ou texte -> chaîne de caractères.
# L'implémentation (pypdf, python-docx) vit dans adapters/outbound/cv/.

from typing import Protocol


class CvExtractorPort(Protocol):
    """Contrat d'un extracteur de texte de CV."""

    def extract_text(self, content: bytes, filename: str) -> str:
        """Retourne le texte brut du CV.

        `filename` sert à détecter le format (extension). Lève `CvExtractionError`
        si le format n'est pas supporté ou si le fichier est illisible.
        """
        ...
