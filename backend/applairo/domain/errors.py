# domain/errors.py
# Erreurs métier, indépendantes de toute technologie.


class JobSearchError(Exception):
    """Erreur récupérable lors d'une recherche d'offres.

    Levée par un adaptateur de recherche (ex: API indisponible, clés invalides).
    """


class CvExtractionError(Exception):
    """Le texte du CV n'a pas pu être extrait (format non supporté, fichier illisible)."""


class ProfileExtractionError(Exception):
    """L'agent n'a pas pu déduire un profil de recherche exploitable du CV."""


class EvaluationError(Exception):
    """Le comité n'a pas pu évaluer les offres (réponse du modèle invalide, quota)."""
