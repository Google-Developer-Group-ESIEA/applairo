# domain/errors.py
# Erreurs métier, indépendantes de toute technologie.


class JobSearchError(Exception):
    """Erreur récupérable lors d'une recherche d'offres.

    Levée par un adaptateur de recherche (ex: API indisponible, clés invalides).
    L'adaptateur ADK la capture et la reformule pour le modèle de langage.
    """
