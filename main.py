import speech_recognition as sr
import pyttsx3
import subprocess
import os
import webbrowser
import threading
import re
import time

from interfaz import InterfazEVA
from eva_inteligencia.observacion import crear_observador
from persistencia import configurar_avisos
from preferencias import cargar_preferencias, guardar_preferencias as persistir_preferencias
from metricas_voz import (
    marcar_fin_captura, medir_primera_respuesta, medir_etapa, medir_procesamiento,
    registrar_duracion, limpiar_captura,
)
from comandos_voz import preparar_comando, normalizar_intencion, es_consulta_hora, es_consulta_fecha, diagnosticar
from aclaraciones_comandos import (
    SeguimientoAclaraciones, es_consulta_personal, preparar_recordatorio, aclaracion_musical,
)
from whisper_control import (
    ControlWhisper, FlujoCancelable, WhisperNoDisponible, USAR_GOOGLE_FALLBACK,
    configurar_captura,
)
from gemini_control import (
    preguntar_gemini, consultar_estado_gemini, guardar_configuracion_gemini,
    probar_conexion_gemini, desconectar_gemini, recargar_gemini,
)
from urllib.parse import quote
from alarmas import (
    crear_alarma,
    detener_alarma
)
from recordatorios import (
    crear_recordatorio,
    iniciar_recordatorios,
    obtener_recordatorios_pendientes,
    eliminar_todos_recordatorios
)
from tiempo_eva import (
    interpretar_hora,
    interpretar_en_minutos,
    interpretar_fecha,
    convertir_numero
)
from datetime import datetime, timedelta


# ==================================================
# SPOTIFY
# ==================================================

from spotify_control import (
    inicializar_spotify,
    consultar_estado,
    guardar_configuracion,
    conectar_spotify,
    desconectar_spotify,
    spotify_disponible,
    reproducir_cancion,
    pausar_musica,
    continuar_musica,
    siguiente_cancion,
    cancion_anterior,
    obtener_cancion_actual,
    cambiar_volumen
)



#EVA SOLO PUEDE HABLAR UNA FRASE A LA VEZ Y EVITA HABLAR AL MISMO TIEMPO QUE OTRA EJECUCION

bloqueo_voz = threading.Lock()

# ==================================================
# CONFIGURACIÓN DE VOZ DE EVA
# ==================================================

reconocedor = sr.Recognizer()
configurar_captura(reconocedor)
# Limitar la espera del fallback de red; no limita la duración de la grabación.
reconocedor.operation_timeout = 8

bloqueo_voz = threading.Lock()


# ==================================================
# EVA HABLA
# ==================================================

def hablar(texto):

    medir_primera_respuesta()
    print("EVA:", texto)

    interfaz.agregar_mensaje(
        "EVA",
        texto
    )

    try:

        # Solo una voz de EVA puede ejecutarse
        # al mismo tiempo
        with bloqueo_voz:

            motor_voz = pyttsx3.init()

            voces = motor_voz.getProperty(
                "voices"
            )

            motor_voz.setProperty(
                "voice",
                voces[0].id
            )

            motor_voz.setProperty(
                "rate",
                170
            )

            motor_voz.setProperty(
                "volume",
                1.0
            )

            motor_voz.say(
                texto
            )

            interfaz.iniciar_actividad("HABLANDO")
            try:
                motor_voz.runAndWait()
            finally:
                interfaz.finalizar_actividad("HABLANDO")

            motor_voz.stop()

    except Exception as error:

        print(
            "ERROR DE VOZ:",
            error
        )


# ==================================================
# EVA ESCUCHA
# ==================================================

def escuchar(al_reconocer=None):
    """Una captura y una fase PROCESANDO, hasta terminar el comando opcional."""
    if whisper.cerrado:
        return ""
    estado = None

    def cambiar_fase(nuevo):
        nonlocal estado
        if estado is not None:
            interfaz.finalizar_actividad(estado)
        estado = nuevo
        if nuevo is not None:
            interfaz.iniciar_actividad(nuevo)

    limpiar_captura()
    try:
        cambiar_fase("PREPARANDO")
        inicio_preparacion = time.perf_counter()
        try:
            with whisper.capturar(), sr.Microphone() as source:
                source.stream = FlujoCancelable(source.stream, lambda: whisper.cerrado)
                # Este segundo descarta audio: no invitar a hablar todavía.
                with medir_etapa("calibracion_s"):
                    reconocedor.adjust_for_ambient_noise(source, duration=1)
                registrar_duracion("preparacion_microfono_s", time.perf_counter() - inicio_preparacion)
                if whisper.cerrado:
                    return ""
                cambiar_fase("ESCUCHANDO")
                print("\nEscuchando...")
                with medir_etapa("captura_listen_s"):
                    audio = reconocedor.listen(source)
                    fin_listen = time.perf_counter()
                    marcar_fin_captura()
                cambiar_fase("PROCESANDO")
        except WhisperNoDisponible:
            return ""
        if whisper.cerrado:
            return ""
        registrar_duracion("listen_a_transcribir_s", time.perf_counter() - fin_listen)
        try:
            try:
                comando = whisper.transcribir(audio)
            except WhisperNoDisponible as error:
                if whisper.cerrado:
                    return ""
                if not USAR_GOOGLE_FALLBACK:
                    interfaz.agregar_mensaje("EVA", f"{error} El fallback de Google está desactivado.")
                    return ""
                interfaz.agregar_mensaje(
                    "EVA", f"{error} Intentando Google con la misma grabación; requiere Internet."
                )
                with medir_etapa("fallback_google_s"):
                    comando = reconocedor.recognize_google(audio, language="es-PE")
        except sr.UnknownValueError:
            if not whisper.cerrado:
                hablar("No pude entender lo que dijiste.")
            return ""
        except sr.RequestError:
            if not whisper.cerrado:
                hablar("No pude conectarme al servicio de reconocimiento de voz.")
            return ""
        except Exception:
            if not whisper.cerrado:
                interfaz.agregar_mensaje("EVA", "No se pudo reconocer la grabación. Inténtalo de nuevo con Hablar.")
            return ""
        if whisper.cerrado:
            return ""
        interfaz.agregar_mensaje("TÚ", comando)
        if comando and al_reconocer is not None:
            al_reconocer(comando)
        return comando
    finally:
        cambiar_fase(None)
        limpiar_captura()


# ==================================================
# MEMORIA DE EVA
# ==================================================

bloqueo_preferencias = threading.Lock()


def guardar_preferencias(cambios, solo_si_vacios=False):
    with bloqueo_preferencias:
        actuales = persistir_preferencias(cambios, solo_si_vacios=solo_si_vacios)
        if actuales is None:
            return False
        # Actualizar la memoria sólo después de confirmar la escritura.
        preferencias.update(actuales)
        return True


preferencias = cargar_preferencias()

interfaz = InterfazEVA()
observador_inteligencia = crear_observador()
configurar_avisos(lambda mensaje: interfaz.agregar_mensaje("EVA", mensaje))
whisper = ControlWhisper(
    informar=lambda texto: interfaz.agregar_mensaje("EVA", texto),
    actividad=lambda activa: (
        interfaz.iniciar_actividad("PREPARANDO") if activa
        else interfaz.finalizar_actividad("PREPARANDO")
    ),
)
def cerrar_servicios():
    try:
        observador_inteligencia.cerrar()
    finally:
        whisper.cerrar()


interfaz.configurar_cierre(cerrar_servicios)
interfaz.ventana.after(0, whisper.iniciar)
interfaz.configurar_gemini(
    consultar_estado_gemini, guardar_configuracion_gemini,
    probar_conexion_gemini, desconectar_gemini,
)
threading.Thread(target=recargar_gemini, daemon=True).start()
interfaz.configurar_spotify(
    consultar_estado, guardar_configuracion, conectar_spotify, desconectar_spotify
)

# Spotify se comprueba sin bloquear la interfaz ni las demás funciones.
threading.Thread(target=inicializar_spotify, daemon=True).start()


# Spotify será la aplicación favorita por defecto
if preferencias.get(
    "aplicacion_favorita",
    ""
) == "":

    guardar_preferencias({"aplicacion_favorita": "spotify"}, solo_si_vacios=True)


# ==================================================
# ABRIR APLICACIONES
# ==================================================

def abrir_aplicacion(aplicacion):

    if aplicacion == "calculadora":

        subprocess.Popen("calc.exe")

        hablar(
            "Abriendo la calculadora."
        )


    elif aplicacion == "bloc de notas":

        subprocess.Popen("notepad.exe")

        hablar(
            "Abriendo el bloc de notas."
        )


    elif aplicacion == "paint":

        subprocess.Popen("mspaint.exe")

        hablar(
            "Abriendo Paint."
        )


    elif aplicacion == "explorador":

        subprocess.Popen("explorer.exe")

        hablar(
            "Abriendo el explorador de archivos."
        )


    elif aplicacion == "chrome":

        ruta_chrome = (
            r"C:\Program Files\Google"
            r"\Chrome\Application\chrome.exe"
        )

        ruta_chrome_2 = (
            r"C:\Program Files (x86)\Google"
            r"\Chrome\Application\chrome.exe"
        )

        if os.path.exists(ruta_chrome):

            subprocess.Popen(
                ruta_chrome
            )

            hablar(
                "Abriendo Google Chrome."
            )

        elif os.path.exists(
            ruta_chrome_2
        ):

            subprocess.Popen(
                ruta_chrome_2
            )

            hablar(
                "Abriendo Google Chrome."
            )

        else:

            hablar(
                "No pude encontrar Google Chrome."
            )


    elif aplicacion == "spotify":

        try:

            os.startfile("spotify:")

            hablar(
                "Abriendo Spotify."
            )

        except Exception:

            hablar(
                "No pude abrir Spotify."
            )


    else:

        hablar(
            f"No sé cómo abrir "
            f"{aplicacion}."
        )


# ==================================================
# CERRAR APLICACIONES
# ==================================================

def cerrar_aplicacion(aplicacion):

    if aplicacion == "calculadora":

        os.system(
            "taskkill /F /IM "
            "CalculatorApp.exe >nul 2>&1"
        )

        os.system(
            "taskkill /F /IM "
            "Calculator.exe >nul 2>&1"
        )

        hablar(
            "Cerrando la calculadora."
        )


    elif aplicacion == "bloc de notas":

        os.system(
            "taskkill /F /IM "
            "notepad.exe >nul 2>&1"
        )

        hablar(
            "Cerrando el bloc de notas."
        )


    elif aplicacion == "paint":

        os.system(
            "taskkill /F /IM "
            "mspaint.exe >nul 2>&1"
        )

        hablar(
            "Cerrando Paint."
        )


    elif aplicacion == "chrome":

        os.system(
            "taskkill /F /IM "
            "chrome.exe >nul 2>&1"
        )

        hablar(
            "Cerrando Google Chrome."
        )


    elif aplicacion == "spotify":

        try:
            resultado = subprocess.run(
                ["taskkill", "/F", "/IM", "Spotify.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=False, timeout=5
            )
            hablar("Cerrando Spotify." if resultado.returncode == 0
                   else "Spotify no está abierto en este equipo.")
        except (OSError, subprocess.SubprocessError):
            hablar("No pude cerrar Spotify.")


    elif aplicacion == "explorador":

        hablar(
            "Por seguridad no cerraré "
            "el proceso principal del "
            "explorador de Windows."
        )


def abrir_sitio(sitio):

    sitios = {
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "wikipedia": "https://es.wikipedia.org",
        "google": "https://www.google.com",
        "github": "https://github.com"
    }

    sitio = sitio.lower().strip()

    if sitio in sitios:

        hablar(f"Abriendo {sitio}.")

        webbrowser.open(
            sitios[sitio]
        )

        return True

    return False


def buscar_internet(busqueda):

    if busqueda != "":

        hablar(
            f"Buscando {busqueda} en Internet."
        )

        busqueda_codificada = quote(
            busqueda
        )

        url = (
            "https://www.google.com/search?q="
            + busqueda_codificada
        )

        webbrowser.open(url)

    else:

        hablar(
            "No me dijiste qué quieres buscar."
        )


# ==================================================
# PROCESAR COMANDOS
# ==================================================

# El procesador consulta esta tabla antes de evaluar cualquier comando.
respuestas_broma = {}
seguimiento_comandos = SeguimientoAclaraciones()


def guardar_recordatorio_validado(datos):
    guardado = crear_recordatorio(datos['texto'], datos['fecha'], datos['hora'], datos['minuto'])
    if not guardado:
        hablar("No pude guardar el recordatorio. Revisa el aviso de almacenamiento.")
        return True
    hablar(f"De acuerdo. Te recordaré {datos['texto']} el {datos['fecha']} "
           f"a las {datos['hora']:02d}:{datos['minuto']:02d}.")
    return True


def reproducir_busqueda_musical(busqueda):
    # Mismo ejecutor tradicional, compartido con la respuesta a una aclaración.
    if not spotify_disponible():
        hablar("Spotify no está configurado en este equipo.")
        return True
    hablar(f"Buscando {busqueda} en Spotify.")
    resultado = reproducir_cancion(busqueda)
    if resultado["exito"]:
        hablar(f"Reproduciendo {resultado['titulo']} de {resultado['artista']}.")
    else:
        hablar(resultado["mensaje"])
    return True


def procesar_comando(comando):
    pregunta_original = comando.strip()
    comando = preparar_comando(comando)
    comando_normalizado = normalizar_intencion(comando)
    comando_limpio = comando
    turno, aclarada = seguimiento_comandos.recibir(comando, datetime.now())

    if comando_limpio in respuestas_broma:
        diagnosticar("intencion", "respuesta_personalizada")
        hablar(respuestas_broma[comando_limpio])
        return

    if aclarada is not None:
        if aclarada['tipo'] == 'recordatorio':
            diagnosticar("intencion", "crear_recordatorio")
            return guardar_recordatorio_validado(aclarada['parametros'])
        if aclarada['tipo'] == 'musica':
            return reproducir_busqueda_musical(aclarada['consulta'])
        hablar(aclarada['mensaje'])
        return True

    if es_consulta_personal(comando):
        hablar("No conozco la fecha ni la hora de ese evento personal. No voy a suponerlas.")
        return True

    # ==================================================
    # HORA
    # ==================================================

    if es_consulta_hora(comando_normalizado):
        diagnosticar("intencion", "hora_local")

        ahora = datetime.now()

        hora_actual = ahora.strftime(
            "%H:%M"
        )

        hablar(
            f"Son las {hora_actual}."
        )

        return


    # ==================================================
    # SALUDOS
    # ==================================================

    if "hola" in comando:

        nombre = preferencias.get(
            "nombre_usuario",
            ""
        )

        if nombre != "":

            hablar(
                f"Hola {nombre}. "
                "¿En qué puedo ayudarte?"
            )

        else:

            hablar(
                "Hola. ¿En qué puedo ayudarte?"
            )


    elif (
        "cómo estás" in comando
        or "como estas" in comando
    ):

        hablar(
            "Estoy funcionando correctamente "
            "y lista para ayudarte."
        )


    elif (
        "cómo te llamas" in comando
        or "como te llamas" in comando
        or "cuál es tu nombre" in comando
        or "cual es tu nombre" in comando
    ):

        hablar(
            "Mi nombre es EVA. "
            "Soy tu asistente virtual."
        )


    elif (
        "quién eres" in comando
        or "quien eres" in comando
    ):

        hablar(
            "Soy EVA, tu asistente "
            "virtual personal."
        )


    # ==================================================
    # ABRIR APLICACIONES
    # ==================================================

    elif (
        "abre la calculadora" in comando_normalizado
        or "abrir calculadora" in comando_normalizado
    ):
        diagnosticar("intencion", "abrir_aplicacion")

        abrir_aplicacion(
            "calculadora"
        )


    elif (
        "abre el bloc de notas" in comando
        or "abrir bloc de notas" in comando
    ):

        abrir_aplicacion(
            "bloc de notas"
        )


    elif (
        "abre paint" in comando
        or "abrir paint" in comando
    ):

        abrir_aplicacion(
            "paint"
        )


    elif (
        "abre el explorador" in comando
        or "abrir explorador" in comando
    ):

        abrir_aplicacion(
            "explorador"
        )


    elif (
        "abre chrome" in comando
        or "abrir chrome" in comando
        or "abre google chrome" in comando
    ):

        abrir_aplicacion(
            "chrome"
        )


    elif (
        "abre spotify" in comando
        or "abrir spotify" in comando
    ):

        abrir_aplicacion(
            "spotify"
        )


    # ==================================================
    # APLICACIÓN FAVORITA
    # ==================================================

    elif (
        "abre mi aplicación favorita" in comando
        or "abre mi aplicacion favorita" in comando
        or "abrir mi aplicación favorita" in comando
        or "abrir mi aplicacion favorita" in comando
    ):

        aplicacion = preferencias.get(
            "aplicacion_favorita",
            ""
        )

        if aplicacion != "":

            hablar(
                f"Tu aplicación favorita "
                f"es {aplicacion}."
            )

            abrir_aplicacion(
                aplicacion
            )

        else:

            hablar(
                "Todavía no sé cuál es "
                "tu aplicación favorita."
            )


    # ==================================================
    # CERRAR APLICACIONES
    # ==================================================

    elif (
        "cierra la calculadora" in comando_normalizado
        or "cerrar calculadora" in comando_normalizado
    ):
        diagnosticar("intencion", "cerrar_aplicacion")

        cerrar_aplicacion(
            "calculadora"
        )


    elif (
        "cierra el bloc de notas" in comando
        or "cerrar bloc de notas" in comando
    ):

        cerrar_aplicacion(
            "bloc de notas"
        )


    elif (
        "cierra paint" in comando
        or "cerrar paint" in comando
    ):

        cerrar_aplicacion(
            "paint"
        )


    elif (
        "cierra chrome" in comando
        or "cerrar chrome" in comando
        or "cierra google chrome" in comando
    ):

        cerrar_aplicacion(
            "chrome"
        )


    elif (
        "cierra spotify" in comando
        or "cerrar spotify" in comando
    ):

        cerrar_aplicacion(
            "spotify"
        )


    # ==================================================
    # APRENDER NOMBRE DEL USUARIO
    # ==================================================

    elif "mi nombre es" in comando:

        nombre = comando.replace(
            "mi nombre es",
            ""
        ).strip()

        if not guardar_preferencias({"nombre_usuario": nombre}):
            hablar("No pude guardar tu nombre. Revisa el aviso de almacenamiento.")
            return True

        hablar(
            f"Mucho gusto, {nombre}. "
            "Recordaré tu nombre."
        )


    elif (
        "cómo me llamo" in comando
        or "como me llamo" in comando
    ):

        nombre = preferencias.get(
            "nombre_usuario",
            ""
        )

        if nombre != "":

            hablar(
                f"Tu nombre es {nombre}."
            )

        else:

            hablar(
                "Todavía no me has dicho "
                "tu nombre."
            )


    # ==================================================
    # APRENDER APLICACIÓN FAVORITA
    # ==================================================

    elif (
        "mi aplicación favorita es" in comando
        or "mi aplicacion favorita es" in comando
    ):

        aplicacion = comando.replace(
            "mi aplicación favorita es",
            ""
        )

        aplicacion = aplicacion.replace(
            "mi aplicacion favorita es",
            ""
        ).strip()

        if not guardar_preferencias({"aplicacion_favorita": aplicacion}):
            hablar("No pude guardar tu aplicación favorita. Revisa el aviso de almacenamiento.")
            return True

        hablar(
            f"Entendido. Recordaré que "
            f"tu aplicación favorita "
            f"es {aplicacion}."
        )


    elif (
        "cuál es mi aplicación favorita" in comando
        or "cual es mi aplicacion favorita" in comando
    ):

        aplicacion = preferencias.get(
            "aplicacion_favorita",
            ""
        )

        if aplicacion != "":

            hablar(
                f"Tu aplicación favorita "
                f"es {aplicacion}."
            )

        else:

            hablar(
                "Todavía no me has dicho "
                "cuál es tu aplicación favorita."
            )


    # ==================================================
    # BUSCAR EN INTERNET
    # ==================================================

    elif (
        comando.startswith("busca ")
        or comando.startswith("buscar ")
        or comando.startswith("busca en internet ")
    ):

        busqueda = comando

        busqueda = busqueda.replace(
            "busca en internet",
            ""
        )

        busqueda = busqueda.replace(
            "buscar",
            ""
        )

        busqueda = busqueda.replace(
            "busca",
            ""
        )

        busqueda = busqueda.strip()

        buscar_internet(
            busqueda
        )



    # ==================================================
    # ELIMINAR TODOS LOS RECORDATORIOS
    # ==================================================

    elif (
        "elimina todos los recordatorios" in comando
        or "eliminar todos los recordatorios" in comando
        or "borra todos los recordatorios" in comando
        or "borrar todos los recordatorios" in comando
        or "borra todos mis recordatorios" in comando
        or "elimina todos mis recordatorios" in comando
    ):

        resultado = eliminar_todos_recordatorios()

        if resultado:
            hablar(
                "He eliminado todos "
                "tus recordatorios."
            )
        else:
            hablar(
                "No pude eliminar "
                "los recordatorios."
            )


    # ==================================================
    # CONSULTAR RECORDATORIOS
    # ==================================================

    elif (
        "qué recordatorios tengo" in comando
        or "que recordatorios tengo" in comando
        or "mis recordatorios" in comando
        or "dime mis recordatorios" in comando
    ):

        pendientes = obtener_recordatorios_pendientes()

        if pendientes is None:
            hablar("No pude leer tus recordatorios. Revisa el aviso de almacenamiento.")
            return True

        if len(pendientes) == 0:

            hablar(
                "No tienes recordatorios pendientes."
            )

        else:

            hablar(
                f"Tienes {len(pendientes)} "
                "recordatorios pendientes."
            )

            for recordatorio in pendientes:

                texto = recordatorio["texto"]
                fecha = recordatorio.get("fecha")
                hora = recordatorio["hora"]
                minuto = recordatorio["minuto"]

                hablar(
                    f"{texto}, "
                    f"el {fecha}, "
                    f"a las "
                    f"{hora:02d}:{minuto:02d}."
                )


    # ==================================================
    # CREAR RECORDATORIOS
    # ==================================================

    elif (
        comando_normalizado.startswith(("recuerdame ", "recordame ", "recuerda me "))
        or comando_normalizado in ("recuerdame", "recordame", "recuerda me")
    ):
        diagnosticar("intencion", "crear_recordatorio")
        # Conservar el contenido original, incluyendo tildes y horas con ':'.
        contenido = re.sub(r"^rec(?:u[eé]rdame|[oó]rdame|uerda\s+me)\b[\s,;:]*",
                           "", comando).strip()

        # ==============================================
        # RECORDATORIO EN / DENTRO DE X MINUTOS U HORAS
        # ==============================================

        if (
            (
                " en " in contenido
                or "dentro de " in contenido
            )
            and (
                "minuto" in contenido
                or "hora" in contenido
            )
        ):

            momento = interpretar_en_minutos(
                contenido
            )

            if momento is None:

                hablar(
                    "No pude entender cuándo "
                    "quieres el recordatorio."
                )

            else:

                hora, minuto = momento

                # Separar actividad del tiempo

                if "dentro de " in contenido:

                    texto = contenido.split(
                        "dentro de ",
                        1
                    )[0].strip()

                else:

                    texto = contenido.split(
                        " en ",
                        1
                    )[0].strip()

                # Obtener cantidad y unidad

                coincidencia = re.search(
                    r"(?:en|dentro de)\s+"
                    r"(\d+|[a-záéíóú]+)\s+"
                    r"(minuto|minutos|hora|horas)",
                    contenido
                )

                if coincidencia is None:

                    hablar(
                        "No pude entender la cantidad "
                        "de tiempo."
                    )

                else:

                    cantidad_texto = coincidencia.group(1)
                    unidad = coincidencia.group(2)

                    if cantidad_texto.isdigit():

                        cantidad = int(
                            cantidad_texto
                        )

                    else:

                        cantidad = convertir_numero(
                            cantidad_texto
                        )

                    if cantidad is None:

                        hablar(
                            "No pude entender la cantidad "
                            "de tiempo."
                        )

                    else:

                        # Convertir horas a minutos

                        if unidad in (
                            "hora",
                            "horas"
                        ):

                            minutos_relativos = (
                                cantidad * 60
                            )

                        else:

                            minutos_relativos = cantidad

                        # Calcular fecha

                        ahora = datetime.now()

                        fecha_hora = ahora + timedelta(
                            minutes=minutos_relativos
                        )

                        fecha = fecha_hora.strftime(
                            "%Y-%m-%d"
                        )

                        # Guardar recordatorio

                        guardado = crear_recordatorio(
                            texto,
                            fecha,
                            hora,
                            minuto
                        )
                        if not guardado:
                            hablar("No pude guardar el recordatorio. Revisa el aviso de almacenamiento.")
                            return True

                        # Crear respuesta natural

                        if unidad in (
                            "hora",
                            "horas"
                        ):

                            if cantidad == 1:
                                tiempo_respuesta = "una hora"
                            else:
                                tiempo_respuesta = (
                                    f"{cantidad} horas"
                                )

                        else:

                            if cantidad == 1:
                                tiempo_respuesta = "un minuto"
                            else:
                                tiempo_respuesta = (
                                    f"{cantidad} minutos"
                                )

                        hablar(
                            f"De acuerdo. "
                            f"Te recordaré {texto} "
                            f"dentro de {tiempo_respuesta}."
                        )

        # ==============================================
        # RECORDATORIO A UNA HORA ESPECÍFICA
        # ==============================================

        else:
            revision = preparar_recordatorio(comando, datetime.now())
            if revision['estado'] == 'propuesta':
                return guardar_recordatorio_validado(revision['parametros'])
            if revision.get('pendiente'):
                if not seguimiento_comandos.guardar(revision['pendiente'], turno):
                    hablar("Llegó otra instrucción. Repite el recordatorio completo para aclararlo.")
                    return True
            hablar(revision['pregunta'])
            return True


    # DETENER ALARMA
    # IMPORTANTE: DEBE IR ANTES DE CREAR ALARMA
    # ==================================================

    elif (
        comando_normalizado == "detener alarma"
        or comando_normalizado == "deten la alarma"
        or comando_normalizado == "detener la alarma"
        or comando_normalizado == "apaga la alarma"
        or comando_normalizado == "apagar alarma"
        or comando_normalizado == "para la alarma"
        or comando_normalizado == "parar alarma"
    ):
        diagnosticar("intencion", "detener_alarma")

        resultado = detener_alarma()

        if resultado:

            hablar(
                "Alarma detenida."
            )

        else:

            hablar(
                "No hay ninguna alarma sonando."
            )


    # ==================================================
    # ALARMAS
    # IMPORTANTE: DEBE ESTAR ANTES DE SPOTIFY
    # ==================================================


    elif (
    "alarma" in comando_normalizado
    or comando_normalizado.startswith("despiertame ")
    ):
        diagnosticar("intencion", "crear_alarma")

        hora_texto = comando

        # ----------------------------------------------
        # Quitar solamente la orden de crear alarma
        # ----------------------------------------------

        frases_alarma = [
            "pon una alarma",
            "pon alarma",
            "poner una alarma",
            "crea una alarma",
            "crear una alarma",
            "programa una alarma",
            "programar una alarma",
            "despiértame",
            "despiertame",
            "alarma"
        ]

        for frase in frases_alarma:

            if hora_texto.startswith(frase):

                hora_texto = hora_texto.replace(
                    frase,
                    "",
                    1
                ).strip()

                break

        # ----------------------------------------------
        # Quitar "a las" o "para las"
        # SIN quitar "de la tarde", "de la noche", etc.
        # ----------------------------------------------

        if hora_texto.startswith("para las "):

            hora_texto = hora_texto.replace(
                "para las ",
                "",
                1
            ).strip()

        elif hora_texto.startswith("a las "):

            hora_texto = hora_texto.replace(
                "a las ",
                "",
                1
            ).strip()

        print(
            "Hora que EVA interpretará:",
            hora_texto
        )

        # ==================================================
        # ALARMA RELATIVA
        # EN / DENTRO DE X MINUTOS U HORAS
        # ==================================================

        if (
            (
                " en " in comando
                or "dentro de " in comando
            )
            and (
                "minuto" in comando
                or "hora" in comando
            )
        ):

            momento = interpretar_en_minutos(
                comando
            )

            if momento is None:

                hablar(
                    "No pude entender dentro "
                    "de cuánto tiempo quieres "
                    "la alarma."
                )

            else:

                hora, minuto = momento

                crear_alarma(
                    hora,
                    minuto,
                    hablar
                )

                hablar(
                    f"De acuerdo. "
                    f"Alarma programada para "
                    f"las {hora:02d}:{minuto:02d}."
                )


        # ==================================================
        # ALARMA A UNA HORA ESPECÍFICA
        # ==================================================

        else:

            momento = interpretar_hora(
                hora_texto
            )

            if momento is None:

                hablar(
                    "No pude entender "
                    "la hora de la alarma."
                )

            else:

                hora, minuto = momento

                crear_alarma(
                    hora,
                    minuto,
                    hablar
                )

                # ------------------------------------------
                # Respuesta natural
                # ------------------------------------------

                if "de la mañana" in hora_texto:

                    periodo = "de la mañana"

                elif "de la tarde" in hora_texto:

                    periodo = "de la tarde"

                elif "de la noche" in hora_texto:

                    periodo = "de la noche"

                else:

                    periodo = ""

                if periodo:

                    hora_respuesta = hora

                    if hora_respuesta > 12:
                        hora_respuesta -= 12

                    hablar(
                        f"Alarma programada para las "
                        f"{hora_respuesta}:{minuto:02d} "
                        f"{periodo}."
                    )

                else:

                    hablar(
                        f"Alarma programada para las "
                        f"{hora:02d}:{minuto:02d}."
                    )


    # ==================================================
    # GUARDAR CANCIÓN FAVORITA
    # ==================================================

    elif (
        "mi canción favorita es" in comando
        or "mi cancion favorita es" in comando
        or "mi música favorita es" in comando
        or "mi musica favorita es" in comando
    ):

        cancion = comando

        frases = [
            "mi canción favorita es",
            "mi cancion favorita es",
            "mi música favorita es",
            "mi musica favorita es"
        ]

        for frase in frases:

            if frase in cancion:

                cancion = cancion.replace(
                    frase,
                    "",
                    1
                ).strip()

                break

        if cancion == "":

            hablar(
                "No entendí cuál es "
                "tu canción favorita."
            )

        else:

            if not guardar_preferencias({"musica_favorita": cancion}):
                hablar("No pude guardar tu canción favorita. Revisa el aviso de almacenamiento.")
                return True

            hablar(
                f"Entendido. Recordaré que "
                f"tu canción favorita es {cancion}."
            )


    # ==================================================
    # PREGUNTAR CANCIÓN FAVORITA
    # ==================================================

    elif (
        "cuál es mi canción favorita" in comando
        or "cual es mi cancion favorita" in comando
        or "qué canción es mi favorita" in comando
        or "que cancion es mi favorita" in comando
    ):

        cancion = preferencias.get(
            "musica_favorita",
            ""
        )

        if cancion != "":

            hablar(
                f"Tu canción favorita es {cancion}."
            )

        else:

            hablar(
                "Todavía no me has dicho "
                "cuál es tu canción favorita."
            )


    # ==================================================
    # REPRODUCIR CANCIÓN FAVORITA
    # ==================================================

    elif (
        comando == "mi canción favorita"
        or comando == "mi cancion favorita"
        or comando == "mi música favorita"
        or comando == "mi musica favorita"
        or "reproduce mi canción favorita" in comando
        or "reproduce mi cancion favorita" in comando
        or "pon mi canción favorita" in comando
        or "pon mi cancion favorita" in comando
        or "ponme mi canción favorita" in comando
        or "ponme mi cancion favorita" in comando
    ):

        cancion = preferencias.get(
            "musica_favorita",
            ""
        )

        if cancion == "":

            hablar(
                "Todavía no sé cuál es "
                "tu canción favorita."
            )

        else:

            if not spotify_disponible():
                hablar("Spotify no está configurado en este equipo.")
                return True

            hablar(
                f"Buscando tu canción favorita, "
                f"{cancion}, en Spotify."
            )

            try:

                resultado = reproducir_cancion(
                    cancion
                )

                if resultado["exito"]:

                    hablar(
                        f"Reproduciendo "
                        f"{resultado['titulo']} "
                        f"de {resultado['artista']}."
                    )

                else:

                    hablar(
                        resultado["mensaje"]
                    )

            except Exception as error:

                # No mostrar datos internos de errores de Spotify.

                hablar(
                    "No pude reproducir "
                    "tu canción favorita."
                )


    # ==================================================
    # REPRODUCIR CUALQUIER CANCIÓN
    # ==================================================

    elif (
        comando.startswith("reproduce ")
        or comando.startswith("reproducir ")
        or comando.startswith("pon ")
        or comando.startswith("ponme ")
        or comando.startswith("quiero escuchar ")
        or comando.startswith("quiero oír ")
        or comando.startswith("quiero oir ")
        or comando.startswith("escuchar ")
    ):

        pregunta = aclaracion_musical(comando)
        if pregunta:
            if not seguimiento_comandos.guardar({'tipo': 'musica'}, turno):
                hablar("Llegó otra instrucción. Repite qué canción quieres escuchar.")
                return True
            hablar(pregunta)
            return True

        busqueda = comando

        frases_inicio = [
            "reproduce ",
            "reproducir ",
            "pon ",
            "ponme ",
            "quiero escuchar ",
            "quiero oír ",
            "quiero oir ",
            "escuchar "
        ]

        for frase in frases_inicio:

            if busqueda.startswith(frase):

                busqueda = busqueda.replace(
                    frase,
                    "",
                    1
                ).strip()

                break

        frases_extra = [
            "la canción ",
            "la cancion ",
            "la música ",
            "la musica "
        ]

        for frase in frases_extra:

            if busqueda.startswith(frase):

                busqueda = busqueda.replace(
                    frase,
                    "",
                    1
                ).strip()

        if busqueda == "":

            hablar(
                "No entendí qué canción "
                "quieres escuchar."
            )

        else:

            return reproducir_busqueda_musical(busqueda)



    # ==================================================
    # SPOTIFY - CANCIÓN ACTUAL
    # ==================================================

    elif (
        "qué canción está sonando" in comando
        or "que cancion esta sonando" in comando
        or "qué canción suena" in comando
        or "que cancion suena" in comando
        or "qué estoy escuchando" in comando
        or "que estoy escuchando" in comando
    ):

        resultado = obtener_cancion_actual()

        if resultado["exito"]:

            if resultado["reproduciendo"]:

                hablar(
                    f"Está sonando "
                    f"{resultado['titulo']} "
                    f"de {resultado['artista']}."
                )

            else:

                hablar(
                    f"Tienes pausada "
                    f"{resultado['titulo']} "
                    f"de {resultado['artista']}."
                )

        else:

            hablar(
                resultado["mensaje"]
            )



    # ==================================================
    # SPOTIFY - PAUSAR
    # ==================================================

    elif (
        "pausa la música" in comando
        or "pausa la musica" in comando
        or "pausar música" in comando
        or "pausar musica" in comando
        or "pausar cancion" in comando
        or "pausa la cancion" in comando
        or "pausa la canción" in comando
    ):

        resultado = pausar_musica()
        hablar("Música pausada." if resultado["exito"] else resultado["mensaje"])

    # ==================================================
    # SPOTIFY - CONTINUAR
    # ==================================================

    elif (
        "continúa la música" in comando
        or "continua la musica" in comando
        or "reanuda la música" in comando
        or "reanuda la musica" in comando
        or "continúa reproduciendo" in comando
        or "continua reproduciendo" in comando
    ):

        resultado = continuar_musica()
        hablar("Continuando la reproducción." if resultado["exito"] else resultado["mensaje"])

    # ==================================================
    # SPOTIFY - SIGUIENTE CANCIÓN
    # ==================================================

    elif (
        "siguiente canción" in comando
        or "siguiente cancion" in comando
        or "siguiente música" in comando
        or "siguiente musica" in comando
    ):

        resultado = siguiente_cancion()
        hablar("Siguiente canción." if resultado["exito"] else resultado["mensaje"])

    # ==================================================
    # SPOTIFY - CANCIÓN ANTERIOR
    # ==================================================

    elif (
        "canción anterior" in comando
        or "cancion anterior" in comando
        or "música anterior" in comando
        or "musica anterior" in comando
    ):

        resultado = cancion_anterior()
        hablar("Volviendo a la canción anterior." if resultado["exito"] else resultado["mensaje"])

    # ==================================================
    # SPOTIFY - CAMBIAR VOLUMEN
    # ==================================================

    elif (
        "volumen al" in comando
        or "volumen a" in comando
    ):

        try:

            # Extraer solamente los números del comando
            numeros = "".join(
                caracter
                for caracter in comando
                if caracter.isdigit()
            )

            if numeros == "":

                hablar(
                    "Dime un volumen entre cero y cien."
                )

            else:

                volumen = int(numeros)

                if volumen < 0 or volumen > 100:

                    hablar(
                        "El volumen debe estar "
                        "entre cero y cien."
                    )

                else:

                    resultado = cambiar_volumen(
                        volumen
                    )

                    if resultado["exito"]:

                        hablar(
                            f"Volumen de Spotify "
                            f"al {volumen} por ciento."
                        )

                    else:

                        hablar(
                            resultado["mensaje"]
                        )

        except ValueError:

            hablar(
                "No pude reconocer el volumen."
            )


    # ==================================================
    # ELIMINAR TODOS LOS RECORDATORIOS
    # ==================================================

    elif (
        "elimina todos los recordatorios" in comando
        or "eliminar todos los recordatorios" in comando
        or "borra todos los recordatorios" in comando
        or "borrar todos los recordatorios" in comando
        or "borra todos mis recordatorios" in comando
        or "elimina todos mis recordatorios" in comando
    ):

        resultado = eliminar_todos_recordatorios()

        if resultado:

            hablar(
                "He eliminado todos "
                "tus recordatorios."
            )

        else:

            hablar(
                "No pude eliminar "
                "los recordatorios."
            )


    # ==================================================
    # FECHA ACTUAL
    # ==================================================

    elif es_consulta_fecha(comando_normalizado):

        ahora = datetime.now()

        dias = [
            "lunes",
            "martes",
            "miércoles",
            "jueves",
            "viernes",
            "sábado",
            "domingo"
        ]

        meses = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre"
        ]

        nombre_dia = dias[
            ahora.weekday()
        ]

        nombre_mes = meses[
            ahora.month - 1
        ]

        hablar(
            f"Hoy es {nombre_dia} "
            f"{ahora.day} de "
            f"{nombre_mes} de "
            f"{ahora.year}."
        )


    # ==================================================
    # ABRIR PÁGINAS WEB
    # ==================================================

    elif (
        "abre youtube" in comando
        or "abrir youtube" in comando
    ):

        abrir_sitio("youtube")


    elif (
        "abre gmail" in comando
        or "abrir gmail" in comando
    ):

        abrir_sitio("gmail")


    elif (
        "abre wikipedia" in comando
        or "abrir wikipedia" in comando
    ):

        abrir_sitio("wikipedia")


    elif (
        "abre google" in comando
        or "abrir google" in comando
    ):

        abrir_sitio("google")


    elif (
        "abre github" in comando
        or "abrir github" in comando
    ):

        abrir_sitio("github")


# ==================================================
    # BÚSQUEDA EN INTERNET
    # ==================================================



    elif (
        comando.startswith("busca ")
        or comando.startswith("buscar ")
        or comando.startswith("busca en google ")
        or comando.startswith("busca en internet ")
        or comando.startswith("busca información sobre ")
        or comando.startswith("busca informacion sobre ")
    ):

        busqueda = comando

        frases = [
            "busca información sobre",
            "busca informacion sobre",
            "busca en internet",
            "busca en google",
            "buscar",
            "busca"
        ]

        for frase in frases:

            if busqueda.startswith(frase):

                busqueda = busqueda.replace(
                    frase,
                    "",
                    1
                ).strip()

                break

        buscar_internet(
            busqueda
        )



    # ==================================================
    # CERRAR EVA
    # ==================================================

    elif (
        "adiós" in comando
        or "adios" in comando
        or "hasta luego" in comando
        or "cerrar eva" in comando
        or "apágate" in comando
        or "apagate" in comando
    ):

        hablar(
            "Hasta luego."
        )

        return False


    # ==================================================
    # COMANDO DESCONOCIDO
    # ==================================================

    else:
        diagnosticar("intencion", "consulta_general")

        hablar(
            preguntar_gemini(pregunta_original)
        )


    return True


def procesar_desde_interfaz(
    comando
):
    # El diagnóstico nunca decide, responde ni ejecuta el comando tradicional.
    try:
        observador_inteligencia.observar(comando, origen="texto")
    except Exception:
        pass
    procesar_comando(
        comando
    )


def escuchar_desde_interfaz():
    def ejecutar(comando):
        try:
            observador_inteligencia.observar(comando, origen="voz")
        except Exception:
            pass
        with medir_procesamiento(procesar_comando):
            procesar_comando(comando)
    escuchar(al_reconocer=ejecutar)

def avisar_recordatorio(texto):

    # EVA habla
    hablar(texto)

    # La voz se conserva; la confirmación procede del aviso visual de Tkinter.
    return interfaz.mostrar_recordatorio(
        texto
    )


# ==================================================
# BUCLE PRINCIPAL
# ==================================================

eva_activa = True

# ==================================================
# INICIAR RECORDATORIOS
# ==================================================

iniciar_recordatorios(
    avisar_recordatorio
)

# ==================================================
# CONECTAR INTERFAZ
# ==================================================

interfaz.configurar_escucha(
    escuchar_desde_interfaz
)

interfaz.configurar_comando(
    procesar_desde_interfaz
)

# ==================================================
# MENSAJE INICIAL
# ==================================================

nombre_usuario = preferencias.get(
    "nombre_usuario",
    ""
)

def saludar_al_iniciar():
    if nombre_usuario != "":
        hablar(f"Hola {nombre_usuario}. Soy EVA y estoy lista para ayudarte.")
    else:
        hablar("Hola. Soy EVA y estoy lista para ayudarte.")


interfaz.ventana.after(
    0,
    lambda: threading.Thread(target=saludar_al_iniciar, daemon=True).start()
)

# ==================================================
# INICIAR EVA
# ==================================================

try:
    interfaz.iniciar()
finally:
    cerrar_servicios()
