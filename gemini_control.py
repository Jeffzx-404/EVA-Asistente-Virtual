"""Fallback de texto opcional. No ejecuta acciones ni conserva conversaciones."""
import threading
import time

MODELO_GEMINI = "gemini-3.6-flash"
NO_CONFIGURADO = "Gemini no está configurado en este equipo."
NO_DISPONIBLE = "No pude consultar Gemini en este momento. Inténtalo más tarde."
ALTA_DEMANDA = "Gemini tiene mucha demanda en este momento. Inténtalo nuevamente en unos segundos."
LIMITE_USO = "Gemini alcanzó un límite de uso. Espera un momento y revisa la cuota de tu proyecto antes de intentarlo otra vez."
OCUPADO = "Estoy procesando otra consulta. Inténtalo nuevamente en unos segundos."
COOLDOWN_SEGUNDOS = 60
EN_COOLDOWN = "Gemini alcanzó temporalmente su límite de uso. Inténtalo nuevamente en unos momentos."
_ultimo_429 = None
_cliente = None
_inicializacion = threading.Lock()
_consulta = threading.Lock()
_clave = ""
_cargado = False
_revision = 0
_estado = "no_configurado"
_mensaje = NO_CONFIGURADO
_origen = ""


def consultar_estado_gemini():
    """Instantánea pública sin claves ni operaciones de disco/red."""
    return {"estado": _estado, "mensaje": _mensaje, "origen": _origen,
            "ocupado": _consulta.locked()}


def recargar_gemini():
    global _clave, _cargado, _cliente, _revision, _estado, _mensaje, _origen
    with _inicializacion:
        _revision += 1
        _cliente = None
        _clave = ""
        _cargado = True
        try:
            from gemini_config import cargar
            _clave, _origen = cargar()
            _estado = "configurado" if _clave else "no_configurado"
            _mensaje = ("Configurado desde " + _origen + ". Pendiente de probar."
                        if _clave else NO_CONFIGURADO)
        except Exception:
            _origen = ""
            _estado = "error"
            _mensaje = "No se pudo leer la configuración local de Gemini. Guarda una nueva clave."


def guardar_configuracion_gemini(clave):
    try:
        from gemini_config import guardar
        with _inicializacion:
            guardar(clave)
        recargar_gemini()
        return {"exito": _estado == "configurado", "mensaje": _mensaje}
    except ValueError as error:
        return {"exito": False, "mensaje": str(error)}
    except Exception:
        return {"exito": False, "mensaje": "No se pudo guardar la configuración de Gemini."}


def desconectar_gemini():
    try:
        from gemini_config import borrar
        with _inicializacion:
            borrar()
        recargar_gemini()
        return {"exito": _estado != "error", "mensaje": _mensaje}
    except Exception:
        return {"exito": False, "mensaje": "No se pudo borrar la configuración local de Gemini."}


def inicializar_gemini():
    """Preparar el cliente sin red; la ausencia del SDK nunca impide iniciar EVA."""
    global _cliente, _estado, _mensaje
    if not _cargado:
        recargar_gemini()
    with _inicializacion:
        if _cliente is not None:
            return True
        clave = _clave
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
            _estado, _mensaje = "error", "No se pudo preparar Gemini. Comprueba que google-genai esté instalado."
            return False


def gemini_disponible():
    """Indica preparación local, sin comprobar internet ni consumir cuota."""
    return _cliente is not None


def preguntar_gemini(texto, *, _prueba=False):
    """Devuelve solo texto y admite una consulta activa, sin cola de espera."""
    global _estado, _mensaje, _ultimo_429
    if not _consulta.acquire(blocking=False):
        return OCUPADO
    revision = None
    try:
        if not isinstance(texto, str) or not texto.strip():
            return "Escribe una pregunta para Gemini."
        # El mismo bloqueo de consultas protege la lectura y escritura del momento.
        # No dormir ni esperar: devolver inmediatamente mientras dure el cooldown.
        if _ultimo_429 is not None and time.monotonic() - _ultimo_429 < COOLDOWN_SEGUNDOS:
            return EN_COOLDOWN
        if not inicializar_gemini():
            return _mensaje
        with _inicializacion:
            revision = _revision
            cliente, clave = _cliente, _clave
            if _prueba:
                _estado, _mensaje = "probando", "Probando conexión con Gemini…"
        respuesta = cliente.models.generate_content(
            model=MODELO_GEMINI,
            contents=texto.strip(),
            config={
                "system_instruction": "Esta es una prueba de conexión. Responde únicamente OK." if _prueba else (
                    "Responde en español con lenguaje sencillo, claro y natural para un asistente de voz. "
                    "Para preguntas generales, ofrece una explicación de aproximadamente 60 a 120 palabras. "
                    "Usa menos palabras si la pregunta se responde claramente en pocas frases. "
                    "Evita relleno, repeticiones, Markdown innecesario y listas largas, salvo que sean realmente útiles. "
                    "Concluye la explicación de forma completa dentro de esa extensión. "
                    "Responde únicamente con texto; no puedes ejecutar acciones en EVA."
                ),
                # 16 tokens agotaban la salida antes de producir texto (MAX_TOKENS).
                "max_output_tokens": 256 if _prueba else 1024,
                # El presupuesto incluye razonamiento y texto; reducir el razonamiento
                # deja margen para las 60 a 120 palabras solicitadas.
                **({} if _prueba else {"thinking_config": {"thinking_level": "minimal"}}),
                "response_mime_type": "text/plain",
            },
        )
        contenido = respuesta.text
        if not isinstance(contenido, str) or not contenido.strip():
            agotado = any(getattr(c.finish_reason, "value", c.finish_reason) == "MAX_TOKENS"
                          for c in (respuesta.candidates or []))
            mensaje = ("Gemini agotó el presupuesto antes de completar la respuesta. Inténtalo con una pregunta más concreta."
                       if agotado else "Gemini no pudo generar una respuesta para esta pregunta.")
            with _inicializacion:
                if revision == _revision:
                    _estado, _mensaje = "error", mensaje
            return mensaje
        contenido = contenido.strip()
        if clave:
            contenido = contenido.replace(clave, "[dato privado]")
        with _inicializacion:
            if revision != _revision:
                return "La configuración de Gemini cambió. Inténtalo nuevamente."
            _estado, _mensaje = "conectado", "Conexión con Gemini verificada."
        return contenido
    except Exception as error:
        # Inspeccionar solo en memoria; nunca imprimir el error completo.
        codigo = getattr(error, "code", None)
        estado = str(getattr(error, "status", "")).upper()
        detalle = str(error).casefold()
        if str(codigo) == "429" or estado == "RESOURCE_EXHAUSTED":
            _ultimo_429 = time.monotonic()
            mensaje = LIMITE_USO
        elif (str(codigo) == "503" or estado == "UNAVAILABLE"
                or any(marca in detalle for marca in
                       ("503", "unavailable", "alta demanda", "high demand"))):
            mensaje = ALTA_DEMANDA
        else:
            mensaje = NO_DISPONIBLE
        with _inicializacion:
            if revision == _revision:
                _estado, _mensaje = "error", mensaje
        return mensaje
    finally:
        _consulta.release()


def probar_conexion_gemini():
    """Llamada mínima y explícita; usar desde un trabajador de la interfaz."""
    resultado = preguntar_gemini("Responde únicamente: OK", _prueba=True)
    return {"exito": _estado == "conectado" and resultado != OCUPADO,
            "mensaje": _mensaje if _estado == "conectado" else resultado}
