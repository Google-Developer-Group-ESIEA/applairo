# app.py
# Point d'entrée de l'application Job Search Agent.
#
# Ce fichier lance l'interface web Gradio et connecte l'agent ADK
# au chat. Chaque message de l'utilisateur est transmis à l'agent
# qui maintient l'historique de la conversation en session ADK.
#
# Le panneau "Profil en cours" à droite montre en temps réel les
# informations collectées par l'agent — c'est l'aspect pédagogique
# qui permet de visualiser comment l'agent structure les données.
#
# Lancement : python app.py
# Interface disponible sur : http://localhost:7860

import os
import asyncio
import uuid
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
# Doit être fait AVANT d'importer l'agent (qui utilise GOOGLE_API_KEY)
load_dotenv()

import gradio as gr
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agent import root_agent

# ---------------------------------------------------------------------------
# Configuration ADK
# ---------------------------------------------------------------------------

# InMemorySessionService stocke l'historique de la conversation en mémoire.
# Chaque utilisateur reçoit un session_id unique pour isoler ses échanges.
APP_NAME = "job_search_agent"
session_service = InMemorySessionService()

# Ordre et libellés des 5 étapes de collecte du profil.
# Utilisé pour alimenter le panneau pédagogique "Profil en cours".
PROFILE_STEPS = [
    ("title",         "💼 Poste recherché"),
    ("location",      "📍 Localisation"),
    ("experience",    "🎯 Niveau d'expérience"),
    ("contract_type", "📄 Type de contrat"),
]


# ---------------------------------------------------------------------------
# Logique ADK
# ---------------------------------------------------------------------------

async def create_session(session_id: str) -> None:
    """Crée une nouvelle session ADK pour un utilisateur.

    Chaque session est identifiée par un UUID unique généré à l'ouverture
    de l'interface, ce qui permet à plusieurs utilisateurs d'utiliser
    l'agent simultanément sans interférence.
    """
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )


async def ask_agent(message: str, session_id: str) -> tuple[str, list]:
    """Envoie un message à l'agent ADK et retourne sa réponse ainsi que
    les événements intermédiaires (appels d'outils, etc.).

    Inclut un mécanisme de retry avec backoff exponentiel pour gérer
    les erreurs 429 (quota Gemini dépassé), fréquentes sur le tier gratuit.

    Args:
        message: Le texte envoyé par l'utilisateur
        session_id: Identifiant unique de la session

    Returns:
        Tuple (réponse_texte, liste_des_événements_outils)
    """
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    user_content = Content(role="user", parts=[Part(text=message)])

    try:
        response_text = ""
        tool_events = []

        # runner.run_async() génère une séquence d'événements ADK.
        # Les retries sur erreur 429 sont gérés nativement par l'agent
        # via generate_content_config (voir agent.py).
        async for event in runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=user_content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text

            # Détection des appels d'outils pour affichage pédagogique
            if hasattr(event, "tool_call") and event.tool_call:
                tool_events.append(event.tool_call)

        return response_text, tool_events

    except Exception as e:
        return f"Erreur : {e}", []


# ---------------------------------------------------------------------------
# Extraction du profil depuis l'historique de conversation
# ---------------------------------------------------------------------------

def extract_profile_from_history(history: list) -> dict:
    """Déduit les informations du profil collectées à partir de l'historique.

    L'agent pose les 5 questions dans un ordre fixe. On peut donc associer
    chaque réponse de l'utilisateur à une étape du profil en comptant
    les échanges (turns).

    Les réponses utilisateur sont aux index pairs de history (0, 2, 4...).
    Le premier message (index 0) est la réponse à la question 1 (poste),
    le second (index 2) à la question 2 (localisation), etc.

    Args:
        history: Liste de messages Gradio au format {"role": ..., "content": ...}

    Returns:
        Dictionnaire avec les champs du profil renseignés (ou None si pas encore collecté)
    """
    profile = {key: None for key, _ in PROFILE_STEPS}

    # Extraire uniquement les messages de l'utilisateur (role == "user")
    # Le premier message de l'utilisateur correspond à la question 1 du profil
    user_messages = [m["content"] for m in history if m.get("role") == "user"]

    step_keys = [key for key, _ in PROFILE_STEPS]
    for i, key in enumerate(step_keys):
        if i < len(user_messages):
            profile[key] = user_messages[i]

    return profile


def render_profile_panel(profile: dict) -> str:
    """Génère le HTML du panneau pédagogique "Profil en cours de collecte".

    Chaque étape affiche :
    - ✅ + la valeur saisie si l'information a été collectée
    - ⏳ + "En attente..." si l'information n'est pas encore connue

    Args:
        profile: Dictionnaire des informations collectées

    Returns:
        Chaîne HTML affichée dans le panneau latéral
    """
    collected = sum(1 for v in profile.values() if v is not None)
    total = len(PROFILE_STEPS)

    # En-tête avec barre de progression
    progress_pct = int((collected / total) * 100)
    html = f"""
    <div style="font-family: sans-serif; padding: 12px;">
        <h3 style="margin: 0 0 8px 0; color: #1f2937;">📋 Profil en cours de collecte</h3>
        <div style="background: #e5e7eb; border-radius: 999px; height: 8px; margin-bottom: 16px;">
            <div style="background: #2563eb; width: {progress_pct}%; height: 100%;
                        border-radius: 999px; transition: width 0.4s ease;"></div>
        </div>
        <p style="color: #6b7280; font-size: 13px; margin: 0 0 12px 0;">
            {collected}/{total} informations collectées
        </p>
    """

    # Liste des étapes
    for key, label in PROFILE_STEPS:
        value = profile.get(key)
        if value:
            icon = "✅"
            value_html = f'<span style="color: #1d4ed8; font-weight: 500;">{value}</span>'
            bg = "#eff6ff"
            border = "#bfdbfe"
        else:
            icon = "⏳"
            value_html = '<span style="color: #9ca3af; font-style: italic;">En attente...</span>'
            bg = "#f9fafb"
            border = "#e5e7eb"

        html += f"""
        <div style="background: {bg}; border: 1px solid {border}; border-radius: 8px;
                    padding: 10px 12px; margin-bottom: 8px;">
            <div style="font-size: 12px; color: #6b7280; margin-bottom: 2px;">{icon} {label}</div>
            <div style="font-size: 14px;">{value_html}</div>
        </div>
        """

    # Message final si profil complet
    if collected == total:
        html += """
        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px;
                    padding: 10px 12px; margin-top: 4px; text-align: center;">
            <span style="color: #16a34a; font-weight: 600;">🚀 Recherche lancée !</span>
        </div>
        """

    html += "</div>"
    return html


# ---------------------------------------------------------------------------
# Construction de l'interface Gradio
# ---------------------------------------------------------------------------

def build_interface():
    """Construit et retourne l'interface Gradio.

    Layout :
    - Colonne gauche (65%) : chat avec l'agent
    - Colonne droite (35%) : panneau pédagogique "Profil en cours"
    """

    with gr.Blocks(title="Job Search Agent — GDG ESIEA") as demo:

        # En-tête
        gr.Markdown(
            """
            # 🔍 Job Search Agent
            **GDG ESIEA** · Propulsé par Google ADK + Gemini 2.0 Flash + Adzuna

            *Discutez avec votre assistant IA pour trouver les offres d'emploi qui correspondent à votre profil.*
            """
        )

        # États persistants par session Gradio
        session_id_state = gr.State(value="")

        with gr.Row():
            # ── Colonne gauche : chat ──────────────────────────────────────
            with gr.Column(scale=65):
                chatbot = gr.Chatbot(
                    label="Chat avec JobBot",
                    height=520,
                    show_label=True,
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=jobbot"),
                )
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="Tapez votre message ici et appuyez sur Entrée...",
                        show_label=False,
                        scale=9,
                        container=False,
                    )
                    send_btn = gr.Button("Envoyer", scale=1, variant="primary")

            # ── Colonne droite : panneau pédagogique ──────────────────────
            with gr.Column(scale=35):
                profile_panel = gr.HTML(
                    value=render_profile_panel({key: None for key, _ in PROFILE_STEPS}),
                    label="Profil",
                )

                # Encadré explicatif pour les participants
                gr.Markdown(
                    """
                    ---
                    ### 🧠 Comment ça fonctionne ?

                    1. **L'agent pose 5 questions** pour construire votre profil
                    2. **Chaque réponse** est capturée et affichée ici en temps réel
                    3. **Dès le profil complet**, l'agent appelle automatiquement l'outil `search_jobs`
                    4. **L'outil interroge l'API Adzuna** et retourne les offres correspondantes

                    ```python
                    # L'outil appelé par l'agent :
                    search_jobs(
                        title=...,
                        location=...,
                        experience=...,
                        skills=...,
                        contract_type=...,
                    )
                    ```
                    """
                )

        # ── Handlers ──────────────────────────────────────────────────────

        async def on_submit(message: str, history: list, session_id: str):
            """Traite un message utilisateur, interroge l'agent, met à jour l'UI."""
            if not message.strip():
                return "", history, render_profile_panel(extract_profile_from_history(history))

            # Ajouter le message utilisateur à l'historique Gradio
            history = history + [{"role": "user", "content": message}]

            # Interroger l'agent ADK
            response, _ = await ask_agent(message, session_id)

            # Ajouter la réponse de l'agent
            history = history + [{"role": "assistant", "content": response}]

            # Mettre à jour le panneau de profil
            profile = extract_profile_from_history(history)
            panel_html = render_profile_panel(profile)

            return "", history, panel_html

        async def on_load():
            """Initialise une session ADK au chargement de la page."""
            sid = str(uuid.uuid4())
            await create_session(sid)

            # Message d'accueil de l'agent
            welcome, _ = await ask_agent("Bonjour !", sid)
            initial_history = [{"role": "assistant", "content": welcome}]

            return sid, initial_history

        # Envoi via bouton ou touche Entrée
        submit_inputs = [user_input, chatbot, session_id_state]
        submit_outputs = [user_input, chatbot, profile_panel]

        send_btn.click(on_submit, inputs=submit_inputs, outputs=submit_outputs)
        user_input.submit(on_submit, inputs=submit_inputs, outputs=submit_outputs)

        # Initialisation au chargement
        demo.load(
            fn=on_load,
            outputs=[session_id_state, chatbot],
        )

    return demo


# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Vérification des clés API au démarrage
    # Vérification : soit clé API Google, soit Vertex AI (ADC)
    using_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1")
    if not using_vertex and not os.getenv("GOOGLE_API_KEY"):
        print("Authentification manquante : definissez GOOGLE_API_KEY")
        print("ou activez Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT).")
        raise SystemExit(1)

    missing = [k for k in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY") if not os.getenv(k)]
    if missing:
        print(f"Cles API manquantes dans .env : {', '.join(missing)}")
        print("Copiez .env.example en .env et remplissez les valeurs.")
        raise SystemExit(1)

    print("Cles API detectees")
    print("Demarrage sur http://localhost:7860")

    app = build_interface()
    app.launch(
        share=False,
        theme=gr.themes.Soft(),
        css="""
            .gradio-container { max-width: 1200px !important; }
            footer { display: none !important; }
        """,
    )
