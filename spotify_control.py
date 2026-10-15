import os
import re
import time
import threading
import logging
from functools import wraps

SCOPES = "user-read-playback-state user-modify-playback-state"
spotify = None
estado_spotify = "no_configurado"
motivo_spotify = "sin_inicializar"
_bloqueo = threading.RLock()
MENSAJE_NO_DISPONIBLE = "Spotify no está configurado en este equipo."


def spotify_disponible():
    return estado_spotify == "conectado" and spotify is not None


def _fallo(mensaje=MENSAJE_NO_DISPONIBLE):
    return {"exito": False, "mensaje": mensaje}


def _registrar_error(error):
    global estado_spotify, motivo_spotify
    codigo = getattr(error, "http_status", None)
    # Un error operativo no desactiva toda la integración.
    if codigo in (400, 403, 404, 429):
        return _fallo("No pude completar la operación en Spotify. Comprueba la reproducción y el dispositivo.")
    sesion_rechazada = (codigo == 401 or
                       getattr(error, "error", None) in ("invalid_grant", "invalid_client"))
    _estado("error", "La sesión fue rechazada. Conecta de nuevo." if sesion_rechazada else "Spotify no está disponible temporalmente.")
    motivo_spotify = "sesion_rechazada" if sesion_rechazada else "servicio_no_disponible"
    return _fallo()


# Cada cambio invalida resultados pendientes de operaciones anteriores.
_configuracion = None
_revision = 0
_conexion_activa = False
_mensaje = "Spotify no configurado."


def consultar_estado():
    # Consulta sin espera: una operación de reproducción puede tener el lock.
    configuracion = _configuracion
    return {"estado": estado_spotify, "mensaje": _mensaje,
            "disponible": spotify_disponible(),
            "configuracion": dict(configuracion) if configuracion else None,
            "ocupado": _conexion_activa}


def _estado(estado, mensaje):
    global estado_spotify, _mensaje
    estado_spotify = estado
    _mensaje = mensaje


def guardar_configuracion(client_id, redirect_uri):
    global _configuracion, _revision, spotify
    from spotify_config import guardar
    with _bloqueo:
        try:
            nueva = guardar(client_id, redirect_uri)
            if nueva != _configuracion:
                _revision += 1
                spotify = None
            _configuracion = nueva
            if not spotify_disponible():
                _estado("configurado", "Configurado · pendiente de conectar")
            return {"exito": True}
        except ValueError as error:
            return _fallo(str(error))


def _autenticacion(configuracion, cache):
    # Nunca permitir que Spotipy solicite autorización desde un comando.
    for nombre in ("spotipy", "spotipy.client", "spotipy.oauth2", "spotipy.cache_handler"):
        logging.getLogger(nombre).disabled = True
    from spotipy.oauth2 import SpotifyPKCE

    class SesionExistente(SpotifyPKCE):
        def get_access_token(self, code=None, check_cache=True):
            if code is not None:
                return super().get_access_token(code=code, check_cache=False)
            token = self.validate_token(self.cache_handler.get_cached_token())
            if not token or not token.get("access_token"):
                raise ValueError("Sesión no disponible")
            return token["access_token"]

    return SesionExistente(**configuracion, scope=SCOPES, open_browser=False,
                          cache_handler=cache, requests_timeout=5)


def _cliente(auth):
    import spotipy
    cliente = spotipy.Spotify(auth_manager=auth, requests_timeout=5,
                              retries=0, status_retries=0)
    cliente.devices()
    return cliente


def inicializar_spotify():
    """Restaura una sesión sin navegador, sin bloquear el hilo gráfico."""
    global _configuracion, spotify
    from spotify_config import cargar, carpeta_local
    with _bloqueo:
        revision = _revision
    try:
        try:
            configuracion = cargar()
        except ValueError as error:
            with _bloqueo:
                if revision == _revision:
                    _estado("error", str(error))
            return
        with _bloqueo:
            if revision != _revision:
                return
            _configuracion = configuracion
            if not configuracion:
                _estado("no_configurado", "Spotify no configurado.")
                return
            _estado("configurado", "Configurado · pendiente de conectar")
        for nombre in ("spotipy", "spotipy.client", "spotipy.oauth2", "spotipy.cache_handler"):
            logging.getLogger(nombre).disabled = True
        from spotify_sesion import SesionProtegida
        from spotipy.cache_handler import MemoryCacheHandler, CacheFileHandler
        # Trabajar en memoria hasta comprobar que el resultado sigue vigente.
        persistencia = SesionProtegida(configuracion)
        token = persistencia.get_cached_token()
        if (not token and not (carpeta_local() / "spotify_sesion_local").exists()
                and not (carpeta_local() / "spotify.json").exists()):
            token = CacheFileHandler().get_cached_token()  # Solo lectura heredada.
        if not token:
            return
        cache = MemoryCacheHandler(token)
        auth = _autenticacion(configuracion, cache)
        cliente = _cliente(auth)
        with _bloqueo:
            if revision == _revision:
                # Las sesiones heredadas se conservan solo en memoria.
                if persistencia.ruta.exists():
                    persistencia.save_token_to_cache(cache.get_cached_token())
                    auth.cache_handler = persistencia
                spotify = cliente
                _estado("conectado", "Conectado")
    except Exception:
        with _bloqueo:
            if revision == _revision:
                _estado("error", "No se pudo recuperar Spotify. Revisa la configuración o conecta de nuevo.")


def conectar_spotify():
    """Única entrada de autorización interactiva; llamar desde un trabajador."""
    global _conexion_activa, _revision, spotify
    with _bloqueo:
        if _conexion_activa:
            return _fallo("Ya hay una conexión en curso.")
        if not _configuracion:
            return _fallo("Guarda primero la configuración de Spotify.")
        _conexion_activa = True
        _revision += 1
        revision = _revision
        configuracion = dict(_configuracion)
        spotify = None
        _estado("conectando", "Autoriza Spotify en el navegador. Espera máxima: 120 segundos.")
    try:
        import secrets
        import webbrowser
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from urllib.parse import urlsplit, parse_qs
        from spotipy.cache_handler import MemoryCacheHandler
        from spotify_sesion import SesionProtegida
        from spotify_config import carpeta_local, escribir_atomico
        state = secrets.token_urlsafe(32)
        resultado = {}
        uri = urlsplit(configuracion["redirect_uri"])

        class Callback(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                recibido = urlsplit(self.path)
                parametros = parse_qs(recibido.query)
                valido = (recibido.path == uri.path and
                          secrets.compare_digest(parametros.get("state", [""])[0], state))
                if valido:
                    resultado.update(parametros)
                self.send_response(200 if valido else 400)
                self.end_headers()
                self.wfile.write(b"Puedes volver a EVA." if valido else b"Callback no valido.")

        class ServidorCallback(HTTPServer):
            def get_request(self):
                conexion, direccion = super().get_request()
                conexion.settimeout(2)
                return conexion, direccion

            def handle_error(self, request, client_address):
                # No registrar URLs de callback ni detalles de solicitudes.
                pass

        cache = MemoryCacheHandler()
        auth = _autenticacion(configuracion, cache)
        with ServidorCallback(("127.0.0.1", uri.port), Callback) as servidor:
            servidor.timeout = 0.5
            if not webbrowser.open(auth.get_authorize_url(state=state)):
                raise ValueError("No se pudo abrir el navegador.")
            limite = time.monotonic() + 120
            while not resultado and time.monotonic() < limite:
                with _bloqueo:
                    if revision != _revision:
                        return _fallo("La conexión fue cancelada por un cambio de configuración.")
                servidor.handle_request()
        if "error" in resultado:
            raise ValueError("Autorización rechazada o cancelada.")
        codigo = resultado.get("code", [None])[0]
        if not codigo:
            raise ValueError("No se recibió una autorización válida a tiempo.")
        auth.get_access_token(code=codigo, check_cache=False)
        cliente = _cliente(auth)
        with _bloqueo:
            if revision != _revision:
                return _fallo("La configuración cambió; conecta de nuevo.")
            persistencia = SesionProtegida(configuracion)
            persistencia.save_token_to_cache(cache.get_cached_token())
            escribir_atomico(carpeta_local() / "spotify_sesion_local", b"1")
            auth.cache_handler = persistencia
            spotify = cliente
            _estado("conectado", "Conectado")
        return {"exito": True}
    except Exception:
        with _bloqueo:
            if revision == _revision:
                _estado("error", "No se pudo conectar. Revisa internet, el Redirect URI y el puerto; autoriza antes de 120 segundos.")
        return _fallo("No se pudo conectar con Spotify. Puedes intentarlo de nuevo.")
    finally:
        with _bloqueo:
            _conexion_activa = False


def desconectar_spotify():
    global spotify, _revision
    with _bloqueo:
        _revision += 1
        spotify = None
        try:
            from spotify_sesion import borrar
            borrar()
            _estado("configurado" if _configuracion else "no_configurado",
                    "Configurado · pendiente de conectar" if _configuracion else "Spotify no configurado.")
            return {"exito": True}
        except Exception:
            _estado("error", "Sesión desactivada, pero no se pudo borrar del disco. Intenta desconectar otra vez.")
            return _fallo("No se pudo eliminar la sesión local.")


def _operacion_segura(funcion=None, *, consulta=False):
    """Las consultas auxiliares conservan None; los comandos usan resultados."""
    def decorar(operacion):
        @wraps(operacion)
        def ejecutar(*args, **kwargs):
            if not spotify_disponible():
                return None if consulta else _fallo()
            with _bloqueo:
                if not spotify_disponible():
                    return None if consulta else _fallo()
                try:
                    resultado = operacion(*args, **kwargs)
                    return resultado if consulta or resultado is not None else {"exito": True}
                except Exception as error:
                    resultado = _registrar_error(error)
                    return None if consulta else resultado
        return ejecutar
    return decorar(funcion) if funcion is not None else decorar


def _buscar_cancion(nombre):

    resultado = spotify.search(
        q=nombre,
        type="track",
        limit=10
    )

    canciones = resultado["tracks"]["items"]

    if not canciones:
        return None

    print("\nResultados encontrados:")

    for numero, cancion in enumerate(
        canciones,
        start=1
    ):
        artistas = ", ".join(
            artista["name"]
            for artista in cancion["artists"]
        )

        print(
            numero,
            "-",
            cancion["name"],
            "|",
            artistas
        )

    busqueda = nombre.lower().strip()

    # Quitar expresiones como "de Linkin Park"
    if " de " in busqueda:
        titulo_buscado, artista_buscado = (
            busqueda.split(" de ", 1)
        )
    else:
        titulo_buscado = busqueda
        artista_buscado = ""

    titulo_buscado = titulo_buscado.strip()
    artista_buscado = artista_buscado.strip()

    mejor_cancion = None
    mejor_puntuacion = -1

    for cancion in canciones:

        titulo = cancion["name"].lower().strip()

        artistas = " ".join(
            artista["name"].lower()
            for artista in cancion["artists"]
        )

        puntuacion = 0

        # Título exactamente igual
        if titulo == titulo_buscado:
            puntuacion += 100

        # Título contiene lo buscado
        elif titulo_buscado in titulo:
            puntuacion += 30

        # Artista solicitado
        if (
            artista_buscado
            and artista_buscado in artistas
        ):
            puntuacion += 50

        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_cancion = cancion

    return mejor_cancion


@_operacion_segura(consulta=True)
def buscar_cancion(nombre):
    return _buscar_cancion(nombre)


@_operacion_segura(consulta=True)
def obtener_cancion(nombre):
    cancion = _buscar_cancion(nombre)
    if not cancion:
        return None
    return {"titulo": cancion["name"], "artista": cancion["artists"][0]["name"],
            "uri": cancion["uri"]}


def _obtener_dispositivo():
    dispositivos = spotify.devices()["devices"]
    compatibles = [d for d in dispositivos if not d.get("is_restricted", False)]
    for dispositivo in compatibles:
        if dispositivo.get("is_active"):
            return dispositivo
    for dispositivo in compatibles:
        if dispositivo.get("type", "").lower() == "computer":
            return dispositivo
    return compatibles[0] if compatibles else None


@_operacion_segura(consulta=True)
def obtener_dispositivo():
    return _obtener_dispositivo()


def _informacion_actual(estado):
    cancion = estado["item"]
    return {"exito": True, "titulo": cancion["name"],
            "artista": ", ".join(a["name"] for a in cancion["artists"]),
            "reproduciendo": bool(estado.get("is_playing"))}


@_operacion_segura
def reproducir_cancion(nombre):
    cancion = _buscar_cancion(nombre)
    if not cancion:
        return _fallo("No encontré esa canción.")
    estado = spotify.current_playback()
    if estado and estado.get("is_playing") and estado.get("item"):
        spotify.add_to_queue(cancion["uri"])
        time.sleep(1)
        spotify.next_track()
        time.sleep(2)
    else:
        # Conservar la apertura por URI usada por EVA cuando no hay reproducción.
        # Si falta la app local, la API aún puede controlar otro dispositivo.
        try:
            os.startfile(cancion["uri"])
        except OSError:
            dispositivo = _obtener_dispositivo()
            if not dispositivo:
                return _fallo("No hay un dispositivo Spotify disponible ni pude abrir la aplicación.")
            spotify.start_playback(device_id=dispositivo["id"], uris=[cancion["uri"]])
        time.sleep(5)
    estado_final = spotify.current_playback()
    if (estado_final and estado_final.get("item")
            and estado_final.get("is_playing")
            and estado_final["item"].get("uri") == cancion["uri"]):
        return _informacion_actual(estado_final)
    return _fallo("Spotify recibió la canción, pero no pude confirmar la reproducción.")


@_operacion_segura
def pausar_musica():
    spotify.pause_playback()


@_operacion_segura
def continuar_musica():
    spotify.start_playback()


@_operacion_segura
def siguiente_cancion():
    spotify.next_track()


@_operacion_segura
def cancion_anterior():
    spotify.previous_track()


@_operacion_segura
def obtener_cancion_actual():
    estado = spotify.current_playback()
    if not estado:
        return _fallo("No hay ninguna reproducción activa en Spotify.")
    if not estado.get("item"):
        return _fallo("No pude identificar la canción actual.")
    return _informacion_actual(estado)


@_operacion_segura
def cambiar_volumen(volumen):
    volumen = max(0, min(100, volumen))
    spotify.volume(volumen)
    return {"exito": True, "volumen": volumen}
