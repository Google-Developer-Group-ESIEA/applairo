# tools/adzuna.py
# Outil de recherche d'emploi via l'API Adzuna.
#
# Cet outil est enregistré auprès de l'agent ADK : quand l'agent
# décide de lancer une recherche, il appelle la fonction search_jobs()
# avec les informations collectées auprès de l'utilisateur.
#
# Documentation API Adzuna : https://developer.adzuna.com/docs/search

import os
import requests
from config import RESULTS_PER_PAGE, ADZUNA_COUNTRY


def search_jobs(
    title: str,
    location: str,
    experience: str,
    contract_type: str,
) -> str:
    """Recherche des offres d'emploi sur Adzuna selon le profil de l'utilisateur.

    Cette fonction est appelée automatiquement par l'agent une fois que
    les 4 informations du profil ont été collectées.

    Args:
        title: Intitulé du poste recherché (ex: "Développeur Python")
        location: Ville ou région souhaitée (ex: "Paris", "Lyon")
        experience: Niveau d'expérience (ex: "junior", "senior")
        contract_type: Type de contrat souhaité (ex: "CDI", "stage")

    Returns:
        Chaîne markdown formatée listant les offres trouvées,
        ou un message d'erreur si la recherche échoue.
    """
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        return (
            "Erreur de configuration : les clés API Adzuna sont manquantes. "
            "Vérifiez que ADZUNA_APP_ID et ADZUNA_APP_KEY sont définis dans votre fichier .env."
        )

    # L'API Adzuna (tier gratuit) n'a pas de filtre contract_type dédié.
    # On injecte toutes les informations dans le champ `what` pour une
    # recherche sémantique (ex: "développeur python senior stage Paris").
    what_query = f"{title} {experience} {contract_type}".strip()

    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": what_query,
        "where": location,
        "results_per_page": RESULTS_PER_PAGE,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        return "Erreur : impossible de joindre l'API Adzuna. Vérifiez votre connexion internet."
    except requests.exceptions.HTTPError as e:
        return f"Erreur API Adzuna ({e.response.status_code}) : vérifiez vos clés API."
    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la recherche : {e}"

    results = data.get("results", [])

    if not results:
        return (
            f"Aucune offre trouvée pour « {title} » à « {location} ».\n\n"
            "Suggestions pour élargir votre recherche :\n"
            "- Essayez une ville plus grande ou une région\n"
            "- Simplifiez l'intitulé du poste\n"
            "- Réduisez le nombre de compétences"
        )

    output = f"**{len(results)} offres trouvées pour « {title} » à « {location} »**\n\n"
    output += "---\n\n"

    for i, job in enumerate(results, 1):
        job_title = job.get("title", "Poste non précisé")
        company = job.get("company", {}).get("display_name", "Entreprise non précisée")
        job_location = job.get("location", {}).get("display_name", location)
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        job_url = job.get("redirect_url", "#")

        # Formatage du salaire uniquement si disponible
        if salary_min and salary_max:
            salary_str = f"💰 {int(salary_min):,} – {int(salary_max):,} €/an\n"
        elif salary_min:
            salary_str = f"💰 À partir de {int(salary_min):,} €/an\n"
        else:
            salary_str = ""

        output += f"### {i}. {job_title}\n"
        output += f"🏢 **{company}**\n"
        output += f"📍 {job_location}\n"
        output += salary_str
        output += f"🔗 [Voir l'offre]({job_url})\n\n"

    return output
