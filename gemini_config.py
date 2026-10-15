"""Clave de Gemini por usuario, protegida con DPAPI fuera del repositorio."""
import os
import tempfile
from pathlib import Path


def _ruta():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise ValueError("No se encuentra la carpeta local de Windows.")
    return Path(base) / "EVA" / "gemini_clave.dpapi"


def cargar():
    try:
        ruta = _ruta()
        if ruta.exists():
            import win32crypt
            clave = win32crypt.CryptUnprotectData(ruta.read_bytes(), None, None, None, 1)[1].decode("utf-8")
            if not clave.strip():
                raise ValueError()
            return clave, "local"
        return os.environ.get("GEMINI_API_KEY", "").strip(), "entorno"
    except Exception:
        raise ValueError("No se pudo leer la clave local de Gemini. Guarda una nueva configuración.") from None


def guardar(clave):
    if not isinstance(clave, str) or not clave.strip() or any(c.isspace() for c in clave.strip()):
        raise ValueError("Introduce una API key válida, sin espacios interiores.")
    temporal = None
    try:
        import win32crypt
        ruta = _ruta()
        protegido = win32crypt.CryptProtectData(clave.strip().encode("utf-8"), "EVA Gemini", None, None, None, 1)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=ruta.parent, delete=False) as archivo:
            temporal = Path(archivo.name)
            archivo.write(protegido)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    except Exception:
        raise ValueError("No se pudo guardar la clave protegida de Gemini.") from None
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def borrar():
    try:
        _ruta().unlink(missing_ok=True)
    except Exception:
        raise ValueError("No se pudo borrar la configuración local de Gemini.") from None
