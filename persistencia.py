"""Persistencia local de EVA, sin dependencias ni acceso a credenciales."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time


class ErrorPersistencia(Exception):
    """Error comunicable al usuario sin mostrar datos privados."""


_bloqueo_hilos = threading.RLock()
_bloqueo_avisos = threading.RLock()
_avisos_pendientes = []
_avisos_emitidos = set()
_informar = None
_carpeta_programa = (Path(sys.executable).resolve().parent
                     if getattr(sys, "frozen", False)
                     else Path(__file__).resolve().parent)
_carpeta_inicio = Path.cwd().resolve()


def avisar(mensaje):
    """Conservar los avisos del arranque hasta que exista la interfaz."""
    with _bloqueo_avisos:
        if mensaje in _avisos_emitidos:
            return
        _avisos_emitidos.add(mensaje)
        if _informar is None:
            _avisos_pendientes.append(mensaje)
        else:
            _informar(mensaje)


def configurar_avisos(informar):
    global _informar
    with _bloqueo_avisos:
        _informar = informar
        for mensaje in _avisos_pendientes:
            informar(mensaje)
        _avisos_pendientes.clear()


def ruta_local(nombre):
    # Mismo destino que Spotify y Gemini. Nunca volver al directorio de trabajo.
    base = os.environ.get("LOCALAPPDATA", "")
    if not base or not Path(base).is_absolute():
        raise ErrorPersistencia(
            "No se encuentra LOCALAPPDATA de Windows. EVA no puede guardar "
            "los datos; revisa esa configuración y vuelve a intentarlo."
        )
    return Path(base) / "EVA" / nombre


def rutas_antiguas(nombre):
    return tuple(dict.fromkeys((
        _carpeta_programa / nombre, _carpeta_inicio / nombre,
    )))


def escribir_atomico(ruta, contenido):
    """El llamador mantiene el bloqueo. El temporal vive en el mismo volumen."""
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=ruta.parent, prefix=ruta.name + ".", suffix=".tmp",
            delete=False,
        ) as archivo:
            temporal = Path(archivo.name)
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal is not None:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                avisar(f"No se pudo limpiar un archivo temporal de {ruta.name}. "
                       f"Se conserva en {ruta.parent}; no es el archivo activo.")


@contextmanager
def bloquear(ruta):
    """Serializa hilos y procesos; el SO libera el bloqueo si EVA termina."""
    with _bloqueo_hilos:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        # No eliminar: todas las instancias deben bloquear el mismo archivo.
        with open(ruta.with_name(ruta.name + ".lock"), "a+b") as archivo:
            if os.name == "nt":
                import msvcrt
                limite = time.monotonic() + 10
                while True:
                    try:
                        archivo.seek(0)
                        msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        if time.monotonic() >= limite:
                            raise ErrorPersistencia(
                                f"{ruta.name} está ocupado o no permite acceso. "
                                "No se guardaron cambios. Vuelve a intentarlo."
                            ) from None
                        time.sleep(0.05)
                try:
                    yield
                finally:
                    archivo.seek(0)
                    msvcrt.locking(archivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(archivo.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(archivo.fileno(), fcntl.LOCK_UN)


def _leer_bytes(ruta):
    try:
        return ruta.read_bytes()
    except FileNotFoundError:
        return None


def _constante_invalida(valor):
    raise ValueError("Constante no admitida en JSON")


def _copia_recuperable(ruta, contenido, motivo):
    huella = hashlib.sha256(contenido).hexdigest()
    copia = ruta.with_name(f"{ruta.name}.{motivo}-{huella}.bak")
    existente = _leer_bytes(copia)
    if existente is None:
        escribir_atomico(copia, contenido)
    elif existente != contenido:
        raise ErrorPersistencia(
            f"La copia de recuperación de {ruta.name} fue modificada. "
            "No se sobrescribirá; revisa las copias antes de continuar."
        )
    return copia


class AlmacenJSON:
    def __init__(self, nombre, validar, iniciales, reparar=False):
        self.nombre = nombre
        self.validar = validar
        self.iniciales = iniciales
        self.reparar = reparar
        self._migrado = None

    @contextmanager
    def transaccion(self):
        """Mantener abierta desde la lectura hasta el último guardado."""
        try:
            ruta = ruta_local(self.nombre)
            with bloquear(ruta):
                if self._migrado != ruta:
                    self._migrar(ruta)
                    self._migrado = ruta
                yield ruta
        except OSError:
            raise ErrorPersistencia(
                f"No se pudo leer o guardar {self.nombre}. Revisa los permisos "
                "y el espacio disponible en LOCALAPPDATA\\EVA. "
                "EVA no confirmó cambios; conserva los archivos para recuperarlos."
            ) from None

    def _migrar(self, ruta):
        actual = _leer_bytes(ruta)
        for antigua in rutas_antiguas(self.nombre):
            if antigua.resolve() == ruta.resolve():
                continue
            contenido = _leer_bytes(antigua)
            if contenido is None:
                continue
            if actual is None:
                escribir_atomico(ruta, contenido)
                actual = contenido
                avisar(f"Se migró {self.nombre} a {ruta.parent}. "
                       "El archivo original se conserva en su ubicación anterior.")
            elif contenido != actual:
                copia = _copia_recuperable(ruta, contenido, "migracion")
                avisar(f"Hay versiones distintas de {self.nombre}. EVA mantiene "
                       f"la versión de {ruta.parent}. La versión antigua se "
                       f"conserva también como {copia.name}; revisa ambas "
                       "antes de combinarlas. No se eliminó ningún original.")

    def leer(self, ruta):
        contenido = _leer_bytes(ruta)
        if contenido is None:
            return self.iniciales()
        try:
            datos = json.loads(contenido.decode("utf-8"),
                               parse_constant=_constante_invalida)
            normalizados, valido = self.validar(datos)
        except (ValueError, UnicodeError, RecursionError):
            normalizados, valido = self.iniciales(), False
        if not valido:
            copia = _copia_recuperable(ruta, contenido, "recuperacion")
            mensaje = (f"{self.nombre} contiene datos dañados o incorrectos. "
                       f"Se conserva el original y una copia en {copia}. ")
            if not self.reparar:
                raise ErrorPersistencia(mensaje + "No se modificarán los "
                                        "recordatorios hasta recuperar el archivo.")
            avisar(mensaje + "EVA usará valores seguros para los campos inválidos.")
        return normalizados

    def guardar(self, ruta, datos):
        normalizados, valido = self.validar(datos)
        if not valido:
            raise ErrorPersistencia(
                f"No se guardó {self.nombre}: los datos nuevos son incorrectos."
            )
        try:
            contenido = json.dumps(normalizados, ensure_ascii=False, indent=4,
                                   allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise ErrorPersistencia(
                f"No se guardó {self.nombre}: hay datos que no se pueden "
                "representar como JSON. El archivo anterior se conserva."
            ) from None
        escribir_atomico(ruta, contenido)
