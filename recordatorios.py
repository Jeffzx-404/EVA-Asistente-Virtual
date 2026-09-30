import json
import os
import threading
import time
from datetime import datetime


ARCHIVO_RECORDATORIOS = "recordatorios.json"


# ==================================================
# CARGAR RECORDATORIOS
# ==================================================

def cargar_recordatorios():

    # Si no existe, EVA lo crea automáticamente
    if not os.path.exists(ARCHIVO_RECORDATORIOS):

        guardar_recordatorios([])

        return []

    try:

        with open(
            ARCHIVO_RECORDATORIOS,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(archivo)

    except (json.JSONDecodeError, FileNotFoundError):

        guardar_recordatorios([])

        return []


# ==================================================
# GUARDAR RECORDATORIOS
# ==================================================

def guardar_recordatorios(recordatorios):

    with open(
        ARCHIVO_RECORDATORIOS,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            recordatorios,
            archivo,
            indent=4,
            ensure_ascii=False
        )


# ==================================================
# CREAR RECORDATORIO
# ==================================================

def crear_recordatorio(
    texto,
    fecha,
    hora,
    minuto
):

    recordatorios = cargar_recordatorios()

    nuevo_recordatorio = {
        "texto": texto,
        "fecha": fecha,
        "hora": hora,
        "minuto": minuto,
        "completado": False
    }

    recordatorios.append(
        nuevo_recordatorio
    )

    guardar_recordatorios(
        recordatorios
    )


# ==================================================
# OBTENER RECORDATORIOS PENDIENTES
# ==================================================

def obtener_recordatorios_pendientes():

    recordatorios = cargar_recordatorios()

    return [
        recordatorio
        for recordatorio in recordatorios
        if not recordatorio.get(
            "completado",
            False
        )
    ]


# ==================================================
# VIGILAR RECORDATORIOS
# ==================================================

def iniciar_recordatorios(funcion_aviso):

    def vigilar():

        while True:

            ahora = datetime.now()

            fecha_actual = ahora.strftime(
                "%Y-%m-%d"
            )

            recordatorios = cargar_recordatorios()

            hubo_cambios = False

            for recordatorio in recordatorios:

                if recordatorio.get(
                    "completado",
                    False
                ):
                    continue

                if (
                    recordatorio.get("fecha")
                    == fecha_actual
                    and
                    recordatorio["hora"]
                    == ahora.hour
                    and
                    recordatorio["minuto"]
                    == ahora.minute
                ):

                    funcion_aviso(
                        "Recordatorio. "
                        + recordatorio["texto"]
                    )

                    recordatorio[
                        "completado"
                    ] = True

                    hubo_cambios = True

            if hubo_cambios:

                guardar_recordatorios(
                    recordatorios
                )

            time.sleep(5)

    hilo = threading.Thread(
        target=vigilar,
        daemon=True
    )

    hilo.start()

# ==================================================
# ELIMINAR TODOS LOS RECORDATORIOS
# ==================================================

def eliminar_todos_recordatorios():

    try:

        guardar_recordatorios([])

        return True

    except Exception as error:

        print(
            "Error eliminando recordatorios:",
            error
        )

        return False