"""Fallback de texto opcional. No ejecuta acciones ni conserva conversaciones."""
import os
import threading

MODELO_GEMINI = "gemini-3.6-flash"
NO_CONFIGURADO = "Gemini no está configurado en este equipo."
NO_DISPONIBLE = "No pude consultar Gemini en este momento. Inténtalo más tarde."
ALTA_DEMANDA = "Gemini tiene mucha demanda en este momento. Inténtalo nuevamente en unos segundos."
OCUPADO = "Estoy procesando otra consulta. Inténtalo nuevamente en unos segundos."
_cliente = None
_inicializacion = threading.Lock()
_consulta = threading.Lock()


def inicializar_gemini():
    """Preparar el cliente sin red; la ausencia del SDK nunca impide iniciar EVA."""
    global _cliente
    with _inicializacion:
        if _cliente is not None:
            return True
        clave = os.environ.get("GEMINI_API_KEY", "").strip()
        if not clave:
            return False
        try:
            from google import genai
            from google.genai import types
            _cliente = genai.Client(
                api_key=clave, vertexai=False,
                http_options=types.HttpOptions(
                    timeout=15000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
            return True
        except Exception:
            # No registrar excepciones del SDK: pueden contener datos privados.
            return False


def gemini_disponible():
    """Indica preparación local, sin comprobar internet ni consumir cuota."""
    return _cliente is not None


def preguntar_gemini(texto):
    """Devuelve solo texto y admite una consulta activa, sin cola de espera."""
    if not _consulta.acquire(blocking=False):
        return OCUPADO
    try:
        if not isinstance(texto, str) or not texto.strip():
            return "Escribe una pregunta para Gemini."
        if not inicializar_gemini():
            return NO_CONFIGURADO
        respuesta = _cliente.models.generate_content(
            model=MODELO_GEMINI,
            contents=texto.strip(),
            config={
                "system_instruction": (
                    "Responde en español con lenguaje sencillo, claro y natural para un asistente de voz. "
                    "Para preguntas generales, ofrece una explicación de aproximadamente 120 a 220 palabras, "
                    "distribuidas en 2 a 4 párrafos cortos. Usa menos palabras y párrafos si bastan unas pocas frases. "
                    "Añade más detalle cuando la pregunta lo necesite, sin superar aproximadamente 300 palabras. "
                    "Evita relleno, repeticiones, Markdown innecesario y listas largas, salvo que sean realmente útiles. "
                    "Concluye la explicación de forma completa dentro de esa extensión. "
                    "Responde únicamente con texto; no puedes ejecutar acciones en EVA."
                ),
                "max_output_tokens": 1024,
                "response_mime_type": "text/plain",
            },
        )
        contenido = respuesta.text
        if not isinstance(contenido, str) or not contenido.strip():
            return "Gemini no pudo generar una respuesta para esta pregunta."
        contenido = contenido.strip()
        clave = os.environ.get("GEMINI_API_KEY", "").strip()
        if clave:
            contenido = contenido.replace(clave, "[dato privado]")
        return contenido
    except Exception as error:
        # Inspeccionar solo en memoria; nunca imprimir el error completo.
        codigo = getattr(error, "code", None)
        estado = str(getattr(error, "status", "")).upper()
        detalle = str(error).casefold()
        if (str(codigo) == "503" or estado == "UNAVAILABLE"
                or any(marca in detalle for marca in
                       ("503", "unavailable", "alta demanda", "high demand"))):
            return ALTA_DEMANDA
        return NO_DISPONIBLE
    finally:
        _consulta.release()
