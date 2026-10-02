# Spotify es opcional: EVA funciona aunque no exista config.py.
# Esta plantilla no activa Spotify por sí sola.
# Se necesita un Client ID válido y una sesión previamente autenticada.
# EVA no abre el navegador ni solicita iniciar sesión automáticamente.

SPOTIFY_CLIENT_ID = "TU_CLIENT_ID"

SPOTIFY_REDIRECT_URI = (
    "http://127.0.0.1:8888/callback"
)