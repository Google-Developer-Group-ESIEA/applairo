# Contribuer à Applairo

Merci de votre intérêt pour **Applairo**.
Ce projet est né d'une démo Google Developer Group x ESIEA pour montrer ce
qu'on peut construire avec l'IA aujourd'hui. Les contributions (code, docs,
idées, corrections de bugs) sont les bienvenues, débutants inclus.

En participant, vous acceptez de respecter notre
[Code de Conduite](./CODE_OF_CONDUCT.md).

## Prérequis

- **[Docker](https://docs.docker.com/get-docker/)** + Docker Compose *(voie recommandée)*
- Pour le dev local : **[uv](https://docs.astral.sh/uv/)** (backend Python) et
  **[pnpm](https://pnpm.io/)** + **Node 20** (frontend)
- Des clés API gratuites (voir le [README](./README.md)) : Google AI Studio et Adzuna

## Mise en route

```bash
# 1. Forkez le repo, puis clonez votre fork
git clone git@github.com:<votre-utilisateur>/applairo.git
cd applairo

# 2. Configurez vos clés API
cp .env.example .env   # puis renseignez les variables

# 3a. Tout lancer avec Docker (backend + frontend)
docker compose up --build            # front : http://localhost:3000

# 3b. ...ou en local, service par service
cd backend  && uv sync && uv run uvicorn main:app --reload   # :8000
cd frontend && pnpm install && pnpm dev                      # :3000
```

## Workflow de contribution

1. **Créez une branche** depuis `main` avec un nom parlant :
   ```bash
   git checkout -b feat/ma-fonctionnalite   # ou fix/, docs/, chore/
   ```
2. **Codez** votre changement. Gardez les commits petits et ciblés.
3. **Vérifiez localement** avant de pousser (c'est ce que la CI vérifie aussi) :
   ```bash
   # Backend
   cd backend && uv run ruff check . && \
     uv run python -c "import applairo.adapters.inbound.http.app"   # lint + smoke
   # Frontend
   cd frontend && pnpm build                                        # type-check + build
   ```
4. **Poussez** et ouvrez une **Pull Request** vers `main`.
5. La **CI** doit être verte et au moins **une revue** est requise avant le merge.

## Conventions

- **Commits** : format [Conventional Commits](https://www.conventionalcommits.org/fr/)
  (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- **Style** : le code est linté avec [ruff](https://docs.astral.sh/ruff/).
  Corrigez automatiquement ce qui peut l'être avec `uv run ruff check --fix .`.
- **Langue** : le projet est majoritairement en français (public GDG ESIEA).
  Commentaires et docs en français, noms de variables en anglais, comme
  l'existant.
- **Dépendances** : backend via `uv add <paquet>` (met à jour `pyproject.toml` +
  `uv.lock`), frontend via `pnpm add <paquet>` (dans `frontend/`). Ne modifiez pas
  les lockfiles à la main.

## Signaler un bug ou proposer une idée

Ouvrez une [issue](../../issues/new/choose) en utilisant le bon template.
Plus il y a de contexte (étapes de repro, logs, capture), plus c'est facile
à traiter.

Des questions ? Ouvrez une issue avec le label `question`. On est là pour
aider, surtout si c'est votre première contribution open source.
