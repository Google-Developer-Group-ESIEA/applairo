# adapters/outbound/cv/document_extractor.py
# Adaptateur sortant : extrait le texte brut d'un CV (implémente CvExtractorPort).
#
# Étape purement mécanique, sans LLM :
#   - PDF  -> pypdf
#   - Word -> python-docx (.docx uniquement ; l'ancien .doc binaire n'est pas géré)
#   - Texte -> décodage UTF-8
#
# Le fichier n'est jamais écrit sur disque (le CV est une donnée personnelle) :
# on travaille uniquement sur les octets reçus, en mémoire.

import io
import logging

from docx import Document
from pypdf import PdfReader

from applairo.domain.errors import CvExtractionError

logger = logging.getLogger(__name__)


class DocumentCvExtractor:
    """Extrait le texte d'un CV PDF, Word (.docx) ou texte (implémente CvExtractorPort)."""

    def extract_text(self, content: bytes, filename: str) -> str:
        suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        logger.info(
            "Extraction du CV %r (format détecté: .%s, %d octets)", filename, suffix, len(content)
        )

        if suffix == "pdf":
            text = self._from_pdf(content)
        elif suffix == "docx":
            text = self._from_docx(content)
        elif suffix in ("txt", "md"):
            text = self._from_text(content)
        else:
            raise CvExtractionError(
                f"format .{suffix or '?'} non supporté (attendu : pdf, docx, txt)"
            )

        text = text.strip()
        if not text:
            raise CvExtractionError("le CV semble vide ou illisible")
        logger.info("CV extrait : %d caractères", len(text))
        return text

    @staticmethod
    def _from_pdf(content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:  # pypdf lève des exceptions variées et non typées
            raise CvExtractionError(f"PDF illisible : {exc}") from exc

    @staticmethod
    def _from_docx(content: bytes) -> str:
        try:
            document = Document(io.BytesIO(content))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise CvExtractionError(f"document Word illisible : {exc}") from exc

    @staticmethod
    def _from_text(content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1", errors="replace")
