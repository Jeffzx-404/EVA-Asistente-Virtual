import spotipy
import time
import os

from spotipy.oauth2 import SpotifyPKCE

from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI
)


# ==================================================
# PERMISOS QUE EVA NECESITA
# ==================================================

SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state"
)


# ==================================================
# AUTENTICACIÓN CON SPOTIFY
# ==================================================

autenticacion = SpotifyPKCE(
    client_id=SPOTIFY_CLIENT_ID,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPES,
    open_browser=True
)


spotify = spotipy.Spotify(
    auth_manager=autenticacion
)


# ==================================================
# BUSCAR UNA CANCIÓN
# ==================================================

def buscar_cancion(nombre):

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

# ==================================================
# MOSTRAR INFORMACIÓN DE LA CANCIÓN
# ==================================================

def obtener_cancion(nombre):

    cancion = buscar_cancion(nombre)

    if cancion is None:
        return None

    titulo = cancion["name"]

    artista = cancion["artists"][0]["name"]

    uri = cancion["uri"]

    return {
        "titulo": titulo,
        "artista": artista,
        "uri": uri
    }


# ==================================================
# OBTENER DISPOSITIVO DE SPOTIFY
# ==================================================

def obtener_dispositivo():

    dispositivos = spotify.devices()["devices"]

    if len(dispositivos) == 0:
        return None

    # Buscar primero un dispositivo activo
    for dispositivo in dispositivos:

        if dispositivo["is_active"]:
            return dispositivo

    # Si ninguno está activo, usar el primero disponible
    return dispositivos[0]


# ==================================================
# REPRODUCIR UNA CANCIÓN
# ==================================================

def reproducir_cancion(nombre):

    try:

        # ==========================================
        # 1. BUSCAR CANCIÓN
        # ==========================================

        cancion = buscar_cancion(nombre)

        if cancion is None:
            return {
                "exito": False,
                "mensaje": "No encontré esa canción."
            }

        titulo = cancion["name"]

        artista = ", ".join(
            artista["name"]
            for artista in cancion["artists"]
        )

        uri = cancion["uri"]

        print(
            "Canción encontrada:",
            titulo,
            "-",
            artista
        )

        print(
            "URI:",
            uri
        )

        # ==========================================
        # 2. COMPROBAR SI SPOTIFY YA REPRODUCE
        # ==========================================

        estado = spotify.current_playback()

        if (
            estado
            and estado.get("is_playing")
            and estado.get("item")
        ):

            print("Spotify ya está reproduciendo.")

            # ======================================
            # 3. AÑADIR CANCIÓN A LA COLA
            # ======================================

            print("Añadiendo canción a la cola...")

            spotify.add_to_queue(uri)

            time.sleep(1)

            # ======================================
            # 4. PASAR A LA CANCIÓN
            # ======================================

            print("Cambiando a la canción...")

            spotify.next_track()

            time.sleep(2)

            # ======================================
            # 5. COMPROBAR CANCIÓN REAL
            # ======================================

            estado_final = spotify.current_playback()

            if (
                estado_final
                and estado_final.get("item")
            ):

                actual = estado_final["item"]

                titulo_actual = actual["name"]

                artista_actual = ", ".join(
                    artista["name"]
                    for artista in actual["artists"]
                )

                print(
                    "Spotify está reproduciendo:",
                    titulo_actual,
                    "-",
                    artista_actual
                )

                if estado_final["is_playing"]:

                    return {
                        "exito": True,
                        "titulo": titulo_actual,
                        "artista": artista_actual
                    }

            return {
                "exito": False,
                "mensaje": (
                    "Spotify recibió la canción, "
                    "pero no pude confirmar "
                    "que esté reproduciéndose."
                )
            }

        # ==========================================
        # 6. SPOTIFY CERRADO O SIN REPRODUCCIÓN
        # ==========================================

        print(
            "Spotify no tiene una "
            "reproducción activa."
        )

        print(
            "Abriendo canción mediante URI..."
        )

        os.startfile(uri)

        # Dar tiempo para abrir Spotify
        time.sleep(5)

        # ==========================================
        # 7. COMPROBAR SI COMENZÓ
        # ==========================================

        estado_final = spotify.current_playback()

        if (
            estado_final
            and estado_final.get("item")
            and estado_final["is_playing"]
        ):

            actual = estado_final["item"]

            titulo_actual = actual["name"]

            artista_actual = ", ".join(
                artista["name"]
                for artista in actual["artists"]
            )

            print(
                "Spotify está reproduciendo:",
                titulo_actual,
                "-",
                artista_actual
            )

            return {
                "exito": True,
                "titulo": titulo_actual,
                "artista": artista_actual
            }

        # El URI fue enviado, pero la API
        # todavía no puede confirmarlo.

        return {
            "exito": True,
            "titulo": titulo,
            "artista": artista
        }

    except Exception as error:

        print(
            "Error reproduciendo canción:",
            error
        )

        return {
            "exito": False,
            "mensaje": (
                "No pude reproducir "
                "la canción en Spotify."
            )
        }

# ==================================================
# PAUSAR MÚSICA
# ==================================================

def pausar_musica():

    spotify.pause_playback()


# ==================================================
# CONTINUAR MÚSICA
# ==================================================

def continuar_musica():

    spotify.start_playback()


# ==================================================
# SIGUIENTE CANCIÓN
# ==================================================

def siguiente_cancion():

    spotify.next_track()


# ==================================================
# CANCIÓN ANTERIOR
# ==================================================

def cancion_anterior():

    spotify.previous_track()


# ==================================================
# OBTENER CANCIÓN ACTUAL
# ==================================================

def obtener_cancion_actual():

    try:
        estado = spotify.current_playback()

        if estado is None:
            return {
                "exito": False,
                "mensaje": "No hay ninguna reproducción activa en Spotify."
            }

        if estado.get("item") is None:
            return {
                "exito": False,
                "mensaje": "No pude identificar la canción actual."
            }

        cancion = estado["item"]

        titulo = cancion["name"]

        artistas = ", ".join(
            artista["name"]
            for artista in cancion["artists"]
        )

        reproduciendo = estado["is_playing"]

        return {
            "exito": True,
            "titulo": titulo,
            "artista": artistas,
            "reproduciendo": reproduciendo
        }

    except Exception as error:

        print("Error obteniendo canción:", error)

        return {
            "exito": False,
            "mensaje": "No pude consultar Spotify."
        }

# ==================================================
# CAMBIAR VOLUMEN DE SPOTIFY
# ==================================================

def cambiar_volumen(volumen):

    try:
        # Evitar valores menores que 0 o mayores que 100
        volumen = max(0, min(100, volumen))

        spotify.volume(volumen)

        return {
            "exito": True,
            "volumen": volumen
        }

    except Exception as error:

        print("Error cambiando volumen:", error)

        return {
            "exito": False,
            "mensaje": "No pude cambiar el volumen de Spotify."
        }

def obtener_dispositivo():

    try:
        resultado = spotify.devices()
        dispositivos = resultado["devices"]

        if not dispositivos:
            return None

        # Primero buscar un ordenador
        for dispositivo in dispositivos:

            if (
                dispositivo["type"].lower()
                == "computer"
                and not dispositivo["is_restricted"]
            ):
                return dispositivo

        # Si no encuentra ordenador,
        # utilizar cualquier dispositivo compatible
        for dispositivo in dispositivos:

            if not dispositivo["is_restricted"]:
                return dispositivo

        return None

    except Exception as error:

        print(
            "Error buscando dispositivo:",
            error
        )

        return None