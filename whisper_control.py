"""Whisper opcional: un modelo por sesión en un trabajador privado de EVA.

El proceso permite cancelar una carga o inferencia nativa al cerrar. No importa
main.py, no captura el micrófono y solo intercambia audio en memoria por tuberías.
"""

import base64
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
import threading
import time

from comandos_voz import diagnosticar
from metricas_voz import mediciones_activas, mostrar_mediciones, imprimir_seguro, ram_actual_mb


USAR_GOOGLE_FALLBACK = os.environ.get("EVA_GOOGLE_FALLBACK", "1") != "0"
# Único modelo local. EVA_WHISPER_MODELO ya no selecciona otro modelo.
MODELO_WHISPER = "small"


def configurar_captura(reconocedor):
    """Configuración conservadora; las otras pausas son solo para comparación manual."""
    try:
        pausa = float(os.environ.get("EVA_PAUSA_VOZ", "0.8"))
    except ValueError:
        pausa = 0.8
    reconocedor.pause_threshold = pausa if pausa in (0.8, 0.7, 0.65) else 0.8
    reconocedor.non_speaking_duration = 0.5
    reconocedor.phrase_threshold = 0.3
    reconocedor.energy_threshold = 300
    reconocedor.dynamic_energy_threshold = True


class WhisperNoDisponible(Exception):
    """Mensaje seguro que se puede mostrar sin datos internos ni credenciales."""


class FlujoCancelable:
    """Permite terminar la captura actual al cerrar, sin cortar frases por tiempo."""

    def __init__(self, flujo, cancelado):
        self._flujo = flujo
        self._cancelado = cancelado

    def read(self, size):
        return b"" if self._cancelado() else self._flujo.read(size)

    def close(self):
        self._flujo.close()


def _cargar_modelo():
    # Importación diferida: EVA funciona también sin esta dependencia.
    from faster_whisper import WhisperModel
    from faster_whisper.utils import download_model
    from huggingface_hub.errors import LocalEntryNotFoundError

    cache = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EVA" / "whisper"
    try:
        ruta = download_model(MODELO_WHISPER, cache_dir=str(cache), local_files_only=True,
                              use_auth_token=False)
    except LocalEntryNotFoundError:
        ruta = None
    # Una descarga cancelada puede dejar un snapshot sin todos sus archivos.
    if ruta is None or not all((Path(ruta) / archivo).is_file()
                               for archivo in ("model.bin", "config.json", "tokenizer.json")):
        ruta = download_model(MODELO_WHISPER, cache_dir=str(cache), use_auth_token=False)
    return WhisperModel(ruta, device="cpu", compute_type="int8", num_workers=1,
                        local_files_only=True)


def _transcribir_wav(modelo, wav, metricas=None):
    inicio = time.perf_counter()
    with io.BytesIO(wav) as archivo:
        segmentos, info = modelo.transcribe(
            archivo, language="es", task="transcribe",
            condition_on_previous_text=False, beam_size=5, temperature=0.0,
            # Pista de vocabulario breve; no impone una frase ni una respuesta.
            hotwords="EVA, hora, calculadora, alarma, recuérdame.",
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 700, "speech_pad_ms": 400},
        )
        # Consumir todos los segmentos antes de cerrar BytesIO. No limitar
        # tokens, duración ni cantidad de segmentos de una frase.
        preparado = time.perf_counter()
        texto = "".join(segmento.text for segmento in segmentos).strip()
        fin = time.perf_counter()
        if metricas is not None:
            metricas.update(preprocesado_whisper_s=preparado - inicio,
                            inferencia_s=fin - preparado,
                            audio_s=getattr(info, "duration", None),
                            audio_despues_vad_s=getattr(info, "duration_after_vad", None))
        return texto


def _trabajador():
    def responder(respuesta):
        print(json.dumps(respuesta, ensure_ascii=True), flush=True)

    inicio = time.perf_counter()
    try:
        modelo = _cargar_modelo()
    except ImportError:
        responder({"error": "Whisper no está instalado o faltan dependencias."})
        return
    except Exception:
        responder({"error": "No se pudo cargar el modelo local de Whisper."})
        return
    responder({"listo": True, "carga_s": time.perf_counter() - inicio,
               "ram_mb": ram_actual_mb() if mediciones_activas() else None})
    numero_transcripcion = 0
    try:
        for linea in sys.stdin:
            peticion = json.loads(linea)
            if peticion.get("cerrar"):
                break
            try:
                inicio = time.perf_counter()
                wav = base64.b64decode(peticion["wav"])
                metricas = {"decodificacion_mensaje_s": time.perf_counter() - inicio}
                numero_transcripcion += 1
                metricas["numero_transcripcion"] = numero_transcripcion
                inicio = time.perf_counter()
                texto = _transcribir_wav(modelo, wav, metricas)
                responder({"texto": texto, "transcripcion_s": time.perf_counter() - inicio,
                           **metricas,
                           "ram_mb": ram_actual_mb() if mediciones_activas() else None})
            except Exception:
                responder({"error": "Whisper no pudo transcribir esta grabación."})
    finally:
        del modelo


class ControlWhisper:
    """Control compartido. Los callbacks deben usar la cola de la interfaz."""

    def __init__(self, informar=lambda texto: None, actividad=lambda activa: None):
        self.modelo = MODELO_WHISPER
        self.metricas_carga = {}
        self.metricas_transcripcion = {}
        self._informar = informar
        self._actividad = actividad
        self._bloqueo = threading.Lock()
        self._transcripcion = threading.Lock()
        self._captura = threading.Lock()
        self._cerrado = threading.Event()
        self._respuestas = Queue()
        self._hilo = None
        self._proceso = None
        self._estado = "sin iniciar"
        self._mensaje = "Whisper todavía no está listo."

    @property
    def cerrado(self):
        return self._cerrado.is_set()

    @property
    def estado(self):
        with self._bloqueo:
            return self._estado

    def iniciar(self):
        with self._bloqueo:
            if self._estado != "sin iniciar" or self.cerrado:
                return
            self._estado = "cargando"
            self._inicio_carga = time.perf_counter()
            self._mensaje = "Whisper todavía está cargando el modelo local."
            self._hilo = threading.Thread(target=self._supervisar, name="EVA-Whisper",
                                          daemon=True)
            self._hilo.start()

    @contextmanager
    def capturar(self):
        """Registrar la captura para que cierre espere la liberación del micrófono."""
        with self._captura:
            if self.cerrado:
                raise WhisperNoDisponible("EVA se está cerrando.")
            yield

    def _supervisar(self):
        self._actividad(True)
        imprimir_seguro(f"[Whisper] Modelo: {self.modelo} (multilingue, cpu, int8)")
        self._informar(f"Cargando Whisper local ({self.modelo}). La primera vez descarga el modelo.")
        cargando = True
        try:
            with self._bloqueo:
                if self.cerrado:
                    return
                self._proceso = subprocess.Popen(
                    [sys.executable, "-u", str(Path(__file__).resolve()), "--trabajador"],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                proceso = self._proceso
            respuesta = json.loads(proceso.stdout.readline())
            if not respuesta.get("listo"):
                raise WhisperNoDisponible(respuesta.get("error", "Whisper no está disponible."))
            self.metricas_carga = {
                "carga_s": respuesta.get("carga_s"),
                "arranque_s": time.perf_counter() - self._inicio_carga,
                "ram_mb": respuesta.get("ram_mb"),
            }
            mostrar_mediciones(self.modelo, self.metricas_carga)
            with self._bloqueo:
                if self.cerrado:
                    return
                self._estado = "listo"
            self._actividad(False)
            cargando = False
            self._informar(f"Whisper local listo ({self.modelo}). El reconocimiento local no necesita Internet.")
            for linea in proceso.stdout:
                self._respuestas.put(json.loads(linea))
            if not self.cerrado:
                raise WhisperNoDisponible("El trabajador de Whisper dejó de estar disponible.")
        except Exception as error:
            mensaje = (str(error) if isinstance(error, WhisperNoDisponible)
                       else "Whisper no está disponible en esta sesión.")
            with self._bloqueo:
                if not self.cerrado:
                    self._estado = "error"
                    self._mensaje = mensaje
            if not self.cerrado:
                self._informar(mensaje)
        finally:
            if cargando:
                self._actividad(False)
            self._respuestas.put({"error": "Whisper no está disponible."})

    def transcribir(self, audio, tiempo_limite=60):
        # No esperar una carga ni acumular transcripciones por clics repetidos.
        if not self._transcripcion.acquire(blocking=False):
            raise WhisperNoDisponible("Whisper ya está transcribiendo otro audio.")
        try:
            inicio = time.perf_counter()
            self.metricas_transcripcion = {}
            with self._bloqueo:
                if self.cerrado or self._estado != "listo":
                    raise WhisperNoDisponible(self._mensaje)
                proceso = self._proceso
            inicio_conversion = time.perf_counter()
            wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
            conversion_s = time.perf_counter() - inicio_conversion
            inicio_envio = time.perf_counter()
            peticion = json.dumps({"wav": base64.b64encode(wav).decode("ascii")})
            proceso.stdin.write(peticion + "\n")
            proceso.stdin.flush()
            envio_s = time.perf_counter() - inicio_envio
            limite = time.monotonic() + tiempo_limite
            while not self.cerrado:
                try:
                    respuesta = self._respuestas.get(timeout=0.1)
                except Empty:
                    if time.monotonic() < limite:
                        continue
                    # Descartar el trabajador atascado, sin volver a cargarlo.
                    with self._bloqueo:
                        self._estado = "error"
                        self._mensaje = "Whisper superó el tiempo de transcripción."
                    self._detener_proceso()
                    raise WhisperNoDisponible(self._mensaje)
                if respuesta.get("error"):
                    raise WhisperNoDisponible(respuesta["error"])
                self.metricas_transcripcion = {
                    "conversion_audio_s": conversion_s,
                    "preparacion_envio_s": envio_s,
                    **{clave: respuesta.get(clave) for clave in (
                        "decodificacion_mensaje_s", "preprocesado_whisper_s", "inferencia_s",
                        "audio_s", "audio_despues_vad_s", "numero_transcripcion")},
                    "transcripcion_s": respuesta.get("transcripcion_s"),
                    "transcripcion_total_s": time.perf_counter() - inicio,
                    "ram_mb": respuesta.get("ram_mb"),
                }
                mostrar_mediciones(self.modelo, self.metricas_transcripcion)
                texto = respuesta.get("texto", "")
                diagnosticar("whisper", texto)
                if not texto.strip():
                    raise WhisperNoDisponible("Whisper no detectó palabras en la grabación.")
                return texto
            raise WhisperNoDisponible("EVA se está cerrando.")
        except WhisperNoDisponible:
            raise
        except Exception:
            raise WhisperNoDisponible("Whisper no pudo transcribir esta grabación.") from None
        finally:
            self._transcripcion.release()

    def _detener_proceso(self):
        proceso = self._proceso
        if proceso is not None and proceso.poll() is None:
            proceso.terminate()
            try:
                proceso.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()

    def cerrar(self):
        """Llamar fuera del hilo Tk: salir normalmente o cancelar trabajo nativo."""
        self._cerrado.set()
        # FlujoCancelable termina la lectura y el contexto del micrófono se cierra.
        with self._captura:
            pass
        with self._bloqueo:
            self._estado = "cerrado"
            proceso = self._proceso
        # Solo escribir si nadie está enviando audio por la misma tubería.
        if proceso is not None and self._transcripcion.acquire(blocking=False):
            try:
                if proceso.poll() is None:
                    proceso.stdin.write('{"cerrar": true}\n')
                    proceso.stdin.flush()
                    proceso.wait(timeout=0.5)
            except (OSError, ValueError, subprocess.TimeoutExpired):
                pass
            finally:
                self._transcripcion.release()
        self._detener_proceso()
        if self._hilo is not None:
            self._hilo.join()
        # La terminación del proceso desbloquea también cualquier envío pendiente.
        with self._transcripcion:
            if proceso is not None:
                for canal in (proceso.stdin, proceso.stdout):
                    try:
                        canal.close()
                    except OSError:
                        # Windows puede fallar al vaciar stdin si el hijo ya salió.
                        pass


if __name__ == "__main__" and sys.argv[1:] == ["--trabajador"]:
    _trabajador()
