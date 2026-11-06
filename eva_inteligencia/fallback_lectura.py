"""Fallback opcional: autoriza sólo hora, fecha y ayuda; nunca ejecuta funciones.

Un trabajador daemon reutiliza el modelo oficial. El enrutador tradicional
recibe una intención validada y decide qué función fija llamar. No hay callbacks,
voz, Tkinter, servicios externos ni datos personales en este trabajador.
"""
from dataclasses import dataclass, field
import os
from queue import Empty, Queue
import threading
import time


PERMITIDAS = frozenset(('consultar_hora', 'consultar_fecha', 'ayuda'))


def _cargar_analizador():
    from .integracion import InterpreteLocal
    motor = InterpreteLocal()  # Modelo oficial, sin personalización ni alternativas.
    return lambda texto: motor.proponer(texto, comando_local_atendido=False)


def _autorizar(texto, propuesta):
    from .contexto import analizar_contexto, validar_contexto
    from .parametros import extraer_parametros, validar_accion
    from .seguridad import revisar_seguridad
    if not isinstance(propuesta, dict):
        return None
    intencion = propuesta.get('intencion')
    if (not isinstance(intencion, str) or intencion not in PERMITIDAS
            or propuesta.get('estado') != 'propuesta'
            or propuesta.get('origen') != 'modelo_local'
            or propuesta.get('ejecutable') is not False
            or propuesta.get('parametros') != {}):
        return None
    # Segunda barrera independiente del resultado del clasificador.
    if (revisar_seguridad(texto) or analizar_contexto(texto) is not None
            or validar_contexto(texto, intencion) is not None):
        return None
    validar_accion(intencion, propuesta['parametros'])
    parametros = extraer_parametros(intencion, texto)
    if parametros['estado'] != 'propuesta' or parametros.get('parametros') != {}:
        return None
    return intencion


@dataclass
class _Peticion:
    texto: str
    vence: float
    terminada: threading.Event = field(default_factory=threading.Event)
    intencion: str | None = None


class FallbackLectura:
    def __init__(self, activado=False, *, capacidad=4, espera=5.0):
        if capacidad < 1 or espera <= 0:
            raise ValueError('Capacidad y espera deben ser positivas.')
        self.activado = activado
        self._espera = espera
        self._cola = Queue(maxsize=capacidad)
        self._bloqueo = threading.Lock()
        self._cerrado = threading.Event()
        self._hilo = None
        self._activa = None

    def consultar(self, texto, *, tradicional_reconocido):
        """Llamar desde el hilo de comandos, nunca desde un callback de Tkinter.

        None significa que el enrutador debe conservar su respuesta general.
        Una petición vencida no tiene ejecutor y jamás producirá una respuesta tardía.
        """
        if (not self.activado or tradicional_reconocido is not False or self._cerrado.is_set()
                or not isinstance(texto, str) or not texto.strip() or len(texto) > 1000):
            return None
        peticion = _Peticion(texto, time.monotonic() + self._espera)
        try:
            with self._bloqueo:
                if self._cerrado.is_set():
                    return None
                if self._hilo is None:
                    self._hilo = threading.Thread(target=self._trabajar, name='EVA-FallbackLectura', daemon=True)
                    try:
                        self._hilo.start()
                    except Exception:
                        self._cerrado.set()
                        return None
                self._cola.put_nowait(peticion)
            peticion.terminada.wait(max(0, peticion.vence - time.monotonic()))
            if self._cerrado.is_set() or time.monotonic() >= peticion.vence:
                return None
            return peticion.intencion
        except Exception:
            # Un error del diagnóstico no puede interrumpir el enrutador clásico.
            return None

    def cerrar(self):
        with self._bloqueo:
            self._cerrado.set()
            if self._activa is not None:
                self._activa.terminada.set()
            while True:
                try:
                    pendiente = self._cola.get_nowait()
                    pendiente.terminada.set()
                    self._cola.task_done()
                except Empty:
                    break

    def _trabajar(self):
        analizar = None
        while not self._cerrado.is_set():
            try:
                peticion = self._cola.get(timeout=0.1)
            except Empty:
                continue
            try:
                with self._bloqueo:
                    self._activa = peticion
                if self._cerrado.is_set() or time.monotonic() >= peticion.vence:
                    continue
                if analizar is None:
                    try:
                        analizar = _cargar_analizador()
                    except Exception:
                        # No reintentar una carga fallida en cada consulta ni cambiar de modelo.
                        self.cerrar()
                        return
                if self._cerrado.is_set() or time.monotonic() >= peticion.vence:
                    continue
                try:
                    intencion = _autorizar(peticion.texto, analizar(peticion.texto))
                    if not self._cerrado.is_set() and time.monotonic() < peticion.vence:
                        peticion.intencion = intencion
                except Exception:
                    pass
            finally:
                peticion.terminada.set()
                self._cola.task_done()
                with self._bloqueo:
                    self._activa = None
                peticion = None


def crear_fallback():
    return FallbackLectura(os.environ.get('EVA_INTELIGENCIA_FALLBACK') == '1')
