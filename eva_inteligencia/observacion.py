"""Observador local opcional. Sólo consola; no recibe ejecutores ni objetos Tk.

Importar este módulo no importa sklearn, Whisper, preferencias o personalización.
La cola acotada descarta diagnósticos nuevos al llenarse, nunca comandos de EVA.
"""
import json
import os
from queue import Empty, Full, Queue
import threading
import time


from .modelo_oficial import RUTA_MODELO as MODELO


def _cargar_analizador():
    # Se llama una sola vez, en el trabajador, tras recibir el primer texto.
    from .integracion import InterpreteLocal
    from .diagnostico_whisper import diagnosticar
    motor = InterpreteLocal(MODELO)  # Sin asociaciones personales ni ejecutores.
    return lambda texto: diagnosticar(motor, texto)


def _consola(resultado):
    # Una línea JSON; saltos de línea del texto quedan escapados. Sin archivos.
    print('[EVA observación] ' + json.dumps(resultado, ensure_ascii=True), flush=True)


class ObservadorInteligencia:
    def __init__(self, activado=False, *, capacidad=8, emitir=None):
        if capacidad < 1:
            raise ValueError('La cola debe tener capacidad positiva.')
        self.activado = activado
        self._cola = Queue(maxsize=capacidad)
        self._cerrado = threading.Event()
        self._bloqueo = threading.Lock()
        self._emitir = emitir if emitir is not None else _consola
        self._omitidos = 0
        self._hilo = None
        if activado:
            self._hilo = threading.Thread(target=self._trabajar, name='EVA-Observacion', daemon=True)
            try:
                self._hilo.start()
            except Exception:
                # Incluso un fallo al iniciar el hilo no debe impedir iniciar EVA.
                self._cerrado.set()

    def observar(self, texto, *, origen):
        """Entrega no bloqueante. El resultado nunca decide el comando tradicional."""
        if not self.activado or self._cerrado.is_set():
            return False
        try:
            with self._bloqueo:
                if self._cerrado.is_set():
                    return False
                if not isinstance(texto, str) or not texto.strip() or len(texto) > 1000:
                    self._omitidos += 1
                    return False
                try:
                    self._cola.put_nowait((texto, origen, time.perf_counter()))
                except Full:
                    self._omitidos += 1
                    return False
            return True
        except Exception:
            return False

    def cerrar(self):
        """Descarta textos pendientes sin esperar al modelo ni a la consola.

        Un hilo daemon no puede cancelar inferencia nativa en curso. Al terminarla
        desecha el resultado y sale; nunca mantiene abierta la aplicación.
        """
        with self._bloqueo:
            self._cerrado.set()
            while True:
                try:
                    self._cola.get_nowait()
                    self._cola.task_done()
                except Empty:
                    break

    def _publicar(self, resultado):
        if self._cerrado.is_set():
            return
        with self._bloqueo:
            resultado['diagnosticos_omitidos'] = self._omitidos
        try:
            self._emitir(resultado)
        except Exception:
            # pythonw, consola cerrada o salida no disponible: sin voz ni UI.
            pass

    def _trabajar(self):
        analizar = None
        while not self._cerrado.is_set():
            try:
                elemento = self._cola.get(timeout=0.1)
            except Empty:
                continue
            try:
                if self._cerrado.is_set():
                    continue
                if analizar is None:
                    inicio_carga = time.perf_counter()
                    try:
                        analizar = _cargar_analizador()
                    except Exception:
                        self._publicar(dict(evento='no_disponible', estado='desconocido',
                            motivo='No se pudo cargar el clasificador local. Observación desactivada hasta reiniciar EVA.',
                            ejecutable=False, acciones_ejecutadas=False))
                        self.cerrar()
                        return
                    carga_ms = (time.perf_counter() - inicio_carga) * 1000
                else:
                    carga_ms = 0.0
                if self._cerrado.is_set():
                    continue
                texto, origen, recibido = elemento
                inicio = time.perf_counter()
                try:
                    diagnostico = analizar(texto)
                    # Fallo cerrado incluso si cambia el contrato del adaptador.
                    if diagnostico.get('ejecutable') is not False:
                        raise ValueError('Contrato de sólo diagnóstico no válido.')
                    estado = {'aceptada': 'propuesta', 'aclaracion': 'aclaracion',
                              'desconocida': 'desconocido', 'error': 'desconocido'}[diagnostico['estado']]
                    resultado = dict(intencion_candidata=diagnostico['intencion_candidata'],
                                     estado=estado, parametros=diagnostico['parametros'],
                                     motivo=diagnostico['motivo'])
                except Exception:
                    resultado = dict(intencion_candidata=None, estado='desconocido', parametros=None,
                                     motivo='Falló el análisis local. El procesamiento tradicional continúa sin cambios.')
                resultado.update(texto=texto, origen=origen,
                    interpretacion_ms=(time.perf_counter() - inicio) * 1000,
                    espera_ms=(inicio - recibido) * 1000, carga_modelo_ms=carga_ms,
                    ejecutable=False, acciones_ejecutadas=False)
                self._publicar(resultado)
            finally:
                self._cola.task_done()
                # No conservar el último texto mientras se espera otra petición.
                elemento = texto = resultado = diagnostico = None


def crear_observador():
    """La variable se lee al iniciar EVA; sólo el valor exacto 1 activa el modo."""
    return ObservadorInteligencia(os.environ.get('EVA_DIAGNOSTICO_INTELIGENCIA') == '1')
