import threading
import time
import winsound
from datetime import datetime


alarma_sonando = False


def sonar_alarma():

    global alarma_sonando

    alarma_sonando = True

    print("🔔 ALARMA SONANDO")

    while alarma_sonando:

        winsound.Beep(
            1000,   # frecuencia
            700     # duración en milisegundos
        )

        time.sleep(0.3)


def detener_alarma():

    global alarma_sonando

    if alarma_sonando:

        alarma_sonando = False
        return True

    return False


def crear_alarma(
    hora,
    minuto,
    funcion_aviso
):

    def vigilar_alarma():

        print(
            f"⏰ Alarma programada para "
            f"{hora:02d}:{minuto:02d}"
        )

        while True:

            ahora = datetime.now()

            if (
                ahora.hour == hora
                and ahora.minute == minuto
            ):

                funcion_aviso(
                    "La alarma está sonando."
                )

                sonar_alarma()

                break

            time.sleep(1)

    hilo = threading.Thread(
        target=vigilar_alarma,
        daemon=True
    )

    hilo.start()