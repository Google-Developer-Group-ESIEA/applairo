# Backend Applairo : image basée sur uv (Python 3.12).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Installer les dépendances AVANT le code : cette couche n'est reconstruite que
# si pyproject.toml / uv.lock changent (cache Docker).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code applicatif
COPY . .

# Utiliser directement le venv créé par uv (pas de « uv run » au runtime).
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
