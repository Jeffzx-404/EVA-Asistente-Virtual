"""Sesión protegida por DPAPI para el usuario actual de Windows."""
import hashlib
import json
import win32crypt
from spotify_config import carpeta_local, escribir_atomico


def _identidad(configuracion):
    return hashlib.sha256(json.dumps(configuracion, sort_keys=True).encode()).hexdigest()


class SesionProtegida:
    def __init__(self, configuracion):
        self.identidad = _identidad(configuracion)
        self.ruta = carpeta_local() / "spotify_sesion.dpapi"

    def get_cached_token(self):
        if not self.ruta.exists():
            return None
        try:
            datos = win32crypt.CryptUnprotectData(self.ruta.read_bytes(), None, None, None, 1)[1]
            sesion = json.loads(datos.decode("utf-8"))
            if sesion.get("identidad") == self.identidad:
                return sesion.get("token")
            return None
        except Exception:
            raise ValueError("No se pudo recuperar la sesión protegida. Conecta Spotify de nuevo.") from None

    def save_token_to_cache(self, token_info):
        try:
            datos = json.dumps({"identidad": self.identidad, "token": token_info}).encode("utf-8")
            protegido = win32crypt.CryptProtectData(datos, "EVA Spotify", None, None, None, 1)
            escribir_atomico(self.ruta, protegido)
        except Exception:
            raise ValueError("No se pudo guardar la sesión protegida.") from None


def borrar():
    try:
        # La marca impide reactivar una caché heredada después de desconectar.
        escribir_atomico(carpeta_local() / "spotify_sesion_local", b"1")
        (carpeta_local() / "spotify_sesion.dpapi").unlink(missing_ok=True)
    except Exception:
        raise ValueError("No se pudo eliminar la sesión local.") from None
