# Applairo - backend hexagonal (ports & adapters).
#
# Découpage en couches, du cœur vers l'extérieur :
#   - domain/      : entités métier + ports (interfaces). Aucune dépendance
#                    technique (ni ADK, ni FastAPI, ni HTTP).
#   - application/ : cas d'usage. Orchestre les ports du domaine.
#   - adapters/    : implémentations concrètes des ports (ADK, Adzuna, HTTP).
#   - bootstrap.py : composition root - câble les adaptateurs dans les services.
