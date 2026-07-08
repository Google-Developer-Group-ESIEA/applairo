# main.py
# Point d'entrée du backend Applairo (serveur ASGI).
#
# Lancement local :  uv run uvicorn main:app --reload
# Ou via Docker      (voir docker-compose.yml)
#
# API disponible sur http://localhost:8000  (docs : /docs)

from dotenv import load_dotenv

# Charge le .env local dans l'environnement AVANT de créer l'app.
# Indispensable pour que le SDK Google (google-genai) trouve GOOGLE_API_KEY.
# En Docker, les variables viennent déjà de l'environnement : load_dotenv() est
# alors sans effet.
load_dotenv()

from applairo.adapters.inbound.http.app import create_app  # noqa: E402

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
