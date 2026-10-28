"""Mediciones opcionales sin audio, texto del usuario ni dependencias externas."""

import os
from contextlib import contextmanager
import sys
import threading
import time

_sesion = threading.local()


def mediciones_activas():
    return (os.environ.get("EVA_WHISPER_MEDIR") == "1"
            or os.environ.get("EVA_DIAGNOSTICO_VOZ") == "1")


def registrar_duracion(nombre, segundos):
    if mediciones_activas():
        imprimir_seguro(f"[Voz tiempos] {nombre}={segundos:.6f}")


@contextmanager
def medir_etapa(nombre):
    inicio = time.perf_counter()
    try:
        yield
    finally:
        registrar_duracion(nombre, time.perf_counter() - inicio)


@contextmanager
def medir_procesamiento(procesador):
    """Observar fronteras de llamadas sin cambiar las funciones locales.

    Solo en diagnóstico, solo en este hilo y mientras se ejecuta el procesador.
    No inspecciona argumentos, textos, retornos ni credenciales. Las llamadas
    anidadas no se suman dos veces. Respeta un perfilador externo ya instalado.
    """
    if not mediciones_activas() or sys.getprofile() is not None:
        yield
        return
    nombres = {
        "hablar", "abrir_aplicacion", "cerrar_aplicacion", "abrir_sitio", "buscar_internet",
        "crear_alarma", "detener_alarma", "crear_recordatorio", "eliminar_todos_recordatorios",
        "obtener_recordatorios_pendientes", "guardar_preferencias", "preguntar_gemini",
        "reproducir_cancion", "pausar_musica", "continuar_musica", "siguiente_cancion",
        "cancion_anterior", "obtener_cancion_actual", "cambiar_volumen", "spotify_disponible",
    }
    codigos = {funcion.__code__: nombre for nombre in nombres
               if (funcion := procesador.__globals__.get(nombre)) is not None
               and hasattr(funcion, "__code__")}
    inicio = time.perf_counter()
    llamada = None
    primera = True
    tiempo_acciones = 0.0
    datos = []

    def observar(frame, evento, argumento):
        nonlocal llamada, primera, tiempo_acciones
        if evento == "call" and frame.f_code in codigos and frame.f_back.f_code is procesador.__code__:
            ahora = time.perf_counter()
            nombre = codigos[frame.f_code]
            llamada = (frame, ahora, nombre)
            if primera:
                primera = False
                datos.append(("deteccion_hasta_accion_s", ahora - inicio))
                fin_captura = getattr(_sesion, "fin_listen", None)
                if fin_captura is not None:
                    datos.append(("captura_a_comando_s", ahora - fin_captura))
        elif evento == "return" and llamada is not None and frame is llamada[0]:
            duracion = time.perf_counter() - llamada[1]
            nombre = llamada[2]
            tiempo_acciones += duracion
            tipo = ("respuesta_voz" if nombre == "hablar" else
                    "servicio_externo" if nombre in {"preguntar_gemini", "reproducir_cancion",
                    "pausar_musica", "continuar_musica", "siguiente_cancion", "cancion_anterior",
                    "obtener_cancion_actual", "cambiar_volumen", "spotify_disponible"} else "accion_local")
            datos.append((f"{tipo}_{nombre}_s", duracion))
            llamada = None

    sys.setprofile(observar)
    try:
        yield
    finally:
        sys.setprofile(None)
        total = time.perf_counter() - inicio
        datos.append(("normalizacion_deteccion_s", max(0.0, total - tiempo_acciones)))
        datos.append(("procesamiento_comando_total_s", total))
        # Imprimir después de ejecutar, para no añadir consola a la latencia.
        for nombre, duracion in datos:
            registrar_duracion(nombre, duracion)
        limpiar_captura()


def limpiar_captura():
    _sesion.fin_listen = None
    _sesion.fin_captura = None


def imprimir_seguro(texto):
    try:
        print(texto, flush=True)
    except (OSError, UnicodeError):
        pass


def mostrar_mediciones(modelo, datos):
    if mediciones_activas():
        valores = ", ".join(f"{clave}={valor:.3f}" for clave, valor in datos.items()
                            if isinstance(valor, (int, float)))
        imprimir_seguro(f"[Whisper {modelo}] {valores}")


def marcar_fin_captura():
    _sesion.fin_captura = time.perf_counter() if mediciones_activas() else None
    _sesion.fin_listen = _sesion.fin_captura


def medir_primera_respuesta():
    inicio = getattr(_sesion, "fin_captura", None)
    _sesion.fin_captura = None
    if inicio is None:
        return None
    segundos = time.perf_counter() - inicio
    imprimir_seguro(f"[Voz] captura_a_respuesta_s={segundos:.3f} (antes de voz/interfaz)")
    return segundos


def ram_actual_mb():
    """Working set del proceso actual en MiB; no es la RAM total de EVA."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class Contadores(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (nombre, ctypes.c_size_t) for nombre in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                    "PagefileUsage", "PeakPagefileUsage",
                )
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        consultar = kernel.K32GetProcessMemoryInfo
        consultar.argtypes = [wintypes.HANDLE, ctypes.POINTER(Contadores), wintypes.DWORD]
        consultar.restype = wintypes.BOOL
        datos = Contadores()
        datos.cb = ctypes.sizeof(datos)
        if consultar(kernel.GetCurrentProcess(), ctypes.byref(datos), datos.cb):
            return datos.WorkingSetSize / (1024 * 1024)
    except (OSError, AttributeError):
        pass
    return None
