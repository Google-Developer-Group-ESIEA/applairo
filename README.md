# 🔍 Applairo

**Applairo** — l'agent IA qui transforme votre profil/CV en offres d'emploi ciblées,
puis *(bientôt)* postule pour vous.
Construit avec **Google ADK**, **Gemini 2.5 Flash** et l'**API Adzuna**.

> Né d'une démo du premier événement du **GDG ESIEA**.

---

## Comment ça marche ?

```
Utilisateur  ──► Gradio (UI chat)  ──► Agent ADK (Gemini 2.5 Flash)
                                              │
                                    pose 4 questions
                                              │
                                    ◄── répond une par une
                                              │
                                    profil complet ──► search_jobs()
                                                            │
                                                     API Adzuna
                                                            │
                                                     offres d'emploi
```

1. L'agent pose **4 questions** pour construire votre profil (poste, ville, expérience, contrat)
2. Dès le profil complet, il appelle automatiquement l'outil `search_jobs`
3. L'outil interroge l'API Adzuna en **une seule requête HTTP**
4. Les offres s'affichent dans le chat en markdown

Le panneau latéral de l'interface montre **en temps réel** les informations collectées — c'est l'aspect pédagogique de cette démo.

---

## Architecture du projet

```
applairo/
├── agent.py          # LlmAgent ADK — prompt système + enregistrement des outils
├── tools/
│   └── adzuna.py     # Outil search_jobs — wrapper de l'API Adzuna
├── app.py            # Interface web Gradio — chat + panneau pédagogique
├── config.py         # Constantes configurables (nb d'offres, pays)
├── pyproject.toml    # Métadonnées du projet + dépendances (PEP 621)
└── .env.example      # Template des variables d'environnement
```

---

## Prérequis

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — gestionnaire de paquets et d'environnements Python
- Un compte **Google AI Studio** → [aistudio.google.com](https://aistudio.google.com/) *(gratuit)*
- Un compte **Adzuna Developer** → [developer.adzuna.com](https://developer.adzuna.com/) *(gratuit)*

---

## Installation

### 1. Cloner le repo

```bash
git clone <url-du-repo>
cd applairo
```

### 2. Créer l'environnement virtuel et installer les dépendances

`uv` lit `pyproject.toml`, crée le `.venv` et installe tout en une commande :

```bash
uv sync
```

### 3. Configurer les clés API

```bash
cp .env.example .env
```

Ouvrir `.env` et renseigner :

| Variable | Où l'obtenir |
|---|---|
| `GOOGLE_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `ADZUNA_APP_ID` | [developer.adzuna.com](https://developer.adzuna.com/) → *My Apps* |
| `ADZUNA_APP_KEY` | [developer.adzuna.com](https://developer.adzuna.com/) → *My Apps* |

---

## Lancement

```bash
uv run python app.py
```

L'interface est disponible sur **[http://localhost:7860](http://localhost:7860)**

---

## Configuration

Modifier `config.py` pour ajuster le comportement :

```python
RESULTS_PER_PAGE = 15   # Nombre d'offres retournées (défaut : 15)
ADZUNA_COUNTRY = "fr"   # Pays de recherche : fr, gb, us, de, au...
```

---

## Ressources pour aller plus loin

- [Documentation Google ADK](https://google.github.io/adk-docs/)
- [Documentation API Adzuna](https://developer.adzuna.com/docs/search)
- [Documentation Gradio](https://www.gradio.app/docs)
- [Google AI Studio](https://aistudio.google.com/)
