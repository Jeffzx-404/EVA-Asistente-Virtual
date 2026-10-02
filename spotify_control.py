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
    return estado_spotify == "disponible" and spotify is not None


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
    estado_spotify = "no_autenticado" if sesion_rechazada else "error"
    motivo_spotify = "sesion_rechazada" if sesion_rechazada else "servicio_no_disponible"
    return _fallo()


def inicializar_spotify():
    """Valida una sesión existente sin navegador, consola ni escrituras de caché.

    Puede llamarse de nuevo para reintentar después de recuperar la conexión.
    """
    global spotify, estado_spotify, motivo_spotify
    with _bloqueo:
        spotify = None
        estado_spotify = "comprobando"
        motivo_spotify = "comprobando"
        try:
            import config
            client_id = getattr(config, "SPOTIFY_CLIENT_ID", None)
            redirect_uri = getattr(config, "SPOTIFY_REDIRECT_URI", None)
            if (not isinstance(client_id, str)
                    or not re.fullmatch(r"[0-9a-fA-F]{32}", client_id.strip())
                    or not isinstance(redirect_uri, str)
                    or not redirect_uri.startswith(("http://", "https://"))):
                estado_spotify = "no_configurado"
                motivo_spotify = "configuracion_incompleta"
                return _fallo()
        except Exception:
            estado_spotify = "no_configurado"
            motivo_spotify = "configuracion_no_disponible"
            return _fallo()
        try:
            # Spotipy puede registrar cuerpos de solicitudes con tokens en DEBUG.
            # EVA conserva únicamente las categorías de diagnóstico anteriores.
            for nombre in ("spotipy", "spotipy.client", "spotipy.oauth2",
                           "spotipy.cache_handler"):
                logging.getLogger(nombre).disabled = True
            import spotipy
            from spotipy.oauth2 import SpotifyPKCE
            from spotipy.cache_handler import CacheFileHandler, MemoryCacheHandler
        except Exception:
            estado_spotify = "no_configurado"
            motivo_spotify = "dependencia_no_disponible"
            return _fallo()
        try:
            class SesionExistente(SpotifyPKCE):
                def get_access_token(self, code=None, check_cache=True):
                    token = self.validate_token(self.cache_handler.get_cached_token())
                    if not token or not token.get("access_token"):
                        raise ValueError("Sesion Spotify no disponible")
                    return token["access_token"]

            # Leer la caché existente sin alterarla; renovar solo en memoria.
            cache = MemoryCacheHandler(CacheFileHandler().get_cached_token())
            autenticacion = SesionExistente(
                client_id=client_id.strip(), redirect_uri=redirect_uri,
                scope=SCOPES, open_browser=False, cache_handler=cache,
                requests_timeout=5
            )
            if not cache.get_cached_token():
                estado_spotify = "no_autenticado"
                motivo_spotify = "sin_sesion"
                return _fallo()
            token = autenticacion.validate_token(cache.get_cached_token())
            if not token or not token.get("access_token"):
                estado_spotify = "no_autenticado"
                motivo_spotify = "sesion_no_utilizable"
                return _fallo()
            cliente = spotipy.Spotify(
                auth_manager=autenticacion, requests_timeout=5,
                retries=0, status_retries=0
            )
            cliente.devices()  # Una lista vacía no significa fallo de la API.
            spotify = cliente
            estado_spotify = "disponible"
            motivo_spotify = "sesion_validada"
            return {"exito": True}
        except Exception as error:
            if getattr(error, "error", None) in ("invalid_grant", "invalid_client"):
                estado_spotify = "no_autenticado"
                motivo_spotify = "sesion_rechazada"
            else:
                _registrar_error(error)
                if estado_spotify == "comprobando":
                    estado_spotify = "error"
                    motivo_spotify = "comprobacion_fallida"
            return _fallo()


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
