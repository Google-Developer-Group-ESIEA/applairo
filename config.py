# config.py
# Constantes globales du projet Job Search Agent.
# Modifier RESULTS_PER_PAGE pour contrôler le nombre d'offres retournées.

# Nombre maximum d'offres retournées par l'API Adzuna lors d'une recherche
RESULTS_PER_PAGE = 15

# Code pays pour l'API Adzuna (fr = France)
# Autres options : gb, us, de, au, ca, nl, nz, pl, ru, za
ADZUNA_COUNTRY = "fr"

# Modèle Gemini utilisé par l'agent.
GEMINI_MODEL = "gemini-2.5-flash"

# Nombre de tentatives en cas d'erreur 429 (rate limit)
RETRY_MAX = 3

# Délai initial en secondes entre les tentatives (doublé à chaque essai)
RETRY_DELAY = 5
