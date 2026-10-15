"""Configuración de Spotify por usuario, fuera del proyecto."""
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

REDIRECT_PREDETERMINADO = "http://127.0.0.1:8888/callback"


def carpeta_local():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise ValueError("No se encuentra la carpeta local de Windows.")
    return Path(base) / "EVA"


def validar(client_id, redirect_uri):
    if not isinstance(client_id, str) or not re.fullmatch(r"[a-fA-F0-9]{32}", client_id.strip()):
        raise ValueError("El Client ID debe contener 32 caracteres hexadecimales.")
    try:
        uri = urlsplit(redirect_uri.strip())
        correcto = (uri.scheme == "http" and uri.hostname == "127.0.0.1"
                    and uri.port is not None and 1 <= uri.port <= 65535
                    and uri.path == "/callback" and not uri.query
                    and not uri.fragment and not uri.username and not uri.password)
    except (ValueError, AttributeError):
        correcto = False
    if not correcto:
        raise ValueError("Usa http://127.0.0.1:PUERTO/callback como Redirect URI.")
    return {"client_id": client_id.strip(), "redirect_uri": redirect_uri.strip()}


def escribir_atomico(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(dir=ruta.parent, delete=False) as archivo:
            temporal = Path(archivo.name)
            archivo.write(datos)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def cargar():
    """Un archivo local inválido nunca activa la configuración heredada."""
    try:
        ruta = carpeta_local() / "spotify.json"
        if ruta.exists():
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                return validar(datos["client_id"], datos["redirect_uri"])
            except Exception:
                raise ValueError("La configuración local de Spotify no es válida. Guárdala de nuevo.") from None
        try:
            import config
        except ModuleNotFoundError as error:
            if error.name == "config":
                return None
            raise ValueError("No se pudo leer la configuración anterior.") from None
        return validar(getattr(config, "SPOTIFY_CLIENT_ID", ""),
                       getattr(config, "SPOTIFY_REDIRECT_URI", ""))
    except ValueError:
        raise
    except Exception:
        raise ValueError("No se pudo leer la configuración de Spotify.") from None


def guardar(client_id, redirect_uri):
    datos = validar(client_id, redirect_uri)
    try:
        escribir_atomico(carpeta_local() / "spotify.json",
                        json.dumps(datos, indent=4).encode("utf-8"))
    except Exception:
        raise ValueError("No se pudo guardar la configuración local.") from None
    return datos
