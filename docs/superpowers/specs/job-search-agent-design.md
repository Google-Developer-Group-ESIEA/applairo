# Job Search Agent — Design Spec
*GDG ESIEA — Premier event*
*Date: 2026-07-07*

## Objectif

Agent conversationnel IA qui collecte le profil d'un utilisateur via un dialogue structuré, puis interroge l'API Adzuna pour retourner les offres d'emploi les plus alignées avec ce profil. Démo lors du premier événement GDG ESIEA.

---

## Stack technique

| Composant | Choix |
|---|---|
| Framework agent | Google ADK (Python) |
| LLM | Gemini 2.0 Flash (`gemini-2.0-flash`) |
| API jobs | Adzuna Jobs API (France) |
| Interface web | Gradio (interface chat) |

---

## Architecture

```
GDG_ESIEA_AI_AGENT/
├── agent.py          # LlmAgent ADK + system prompt
├── tools/
│   └── adzuna.py     # outil search_jobs (wrapper Adzuna API)
├── app.py            # interface Gradio
├── config.py         # constantes (RESULTS_PER_PAGE, pays, etc.)
└── .env              # ADZUNA_APP_ID, ADZUNA_APP_KEY, GOOGLE_API_KEY
```

---

## Collecte du profil utilisateur

L'agent pose les questions suivantes, **une à la fois**, dans cet ordre :

1. **Poste recherché** — ex: "Développeur Python", "Data Scientist"
2. **Localisation** — ville ou région (ex: "Paris", "Lyon")
3. **Niveau d'expérience** — junior / intermédiaire / senior
4. **Compétences clés** — liste libre (ex: "Python, Django, SQL")
5. **Type de contrat** — CDI / CDD / stage / alternance

Une fois les 5 champs collectés, l'agent déclenche automatiquement la recherche sans que l'utilisateur ait à le demander.

---

## Outil `search_jobs`

Signature :
```python
def search_jobs(title: str, location: str, experience: str, skills: str, contract_type: str) -> str
```

Requête Adzuna :
```
GET https://api.adzuna.com/v1/api/jobs/fr/search/1
  ?app_id={ADZUNA_APP_ID}
  &app_key={ADZUNA_APP_KEY}
  &what={title} {skills} {contract_type}   ← tout dans `what`, Adzuna n'a pas de filtre contrat natif
  &where={location}
  &results_per_page={RESULTS_PER_PAGE}
```

> Note : l'API Adzuna (tier gratuit) ne propose pas de filtre `contract_type` dédié. Le type de contrat et le niveau d'expérience sont injectés dans le champ `what` pour affiner la recherche sémantique (ex: `what=développeur python senior stage`).

Retourne une chaîne markdown formatée avec pour chaque offre :
- Titre du poste
- Entreprise
- Lieu
- Salaire estimé (si disponible)
- Lien vers l'offre

---

## Configuration (`config.py`)

```python
RESULTS_PER_PAGE = 15   # nombre d'offres retournées par recherche
ADZUNA_COUNTRY = "fr"
```

---

## Flux de données

1. L'utilisateur ouvre l'UI Gradio → l'agent se présente et pose la première question
2. Dialogue : l'agent collecte les 5 champs du profil (une question par tour)
3. Profil complet → l'agent appelle `search_jobs(...)` en une seule requête HTTP
4. Adzuna retourne jusqu'à `RESULTS_PER_PAGE` offres en JSON
5. L'agent formate les résultats en markdown et les affiche dans le chat

---

## Gestion des erreurs

- **Aucun résultat Adzuna** : l'agent l'indique et propose d'élargir les critères (ex: retirer le filtre contrat)
- **API injoignable / erreur HTTP** : message d'erreur clair dans le chat, pas de crash
- **Clés API manquantes** : vérification au démarrage avec message explicite

---

## Qualité du code (repo partagé aux participants)

Le repo sera distribué aux participants du GDG ESIEA comme support pédagogique. À ce titre :

- **Chaque fichier** commence par un commentaire expliquant son rôle dans l'architecture
- **Chaque fonction/outil** est documenté avec une docstring (paramètres, valeur de retour, comportement)
- **Le `README.md`** contient : prérequis, installation, configuration des clés API, et commande de lancement
- **Le `.env.example`** liste toutes les variables d'environnement nécessaires (sans valeurs)
- Le code doit être lisible par quelqu'un qui découvre Google ADK pour la première fois

---

## Hors périmètre

- Authentification utilisateur
- Sauvegarde de profil entre sessions
- Pagination des résultats (au-delà de `RESULTS_PER_PAGE`)
- Tests automatisés (validation manuelle via UI)
