import threading
import time
import winsound
from datetime import datetime, timedelta
from metricas_voz import imprimir_seguro


alarma_sonando = False
_cierre = threading.Event()
_FechaHora = datetime


def sonar_alarma():

    global alarma_sonando

    if _cierre.is_set():
        return
    alarma_sonando = True

    imprimir_seguro("🔔 ALARMA SONANDO")

    while alarma_sonando and not _cierre.is_set():

        winsound.Beep(
            1000,   # frecuencia
            700     # duración en milisegundos
        )

        _cierre.wait(0.3)


def detener_alarma():

    global alarma_sonando

    if alarma_sonando:

        alarma_sonando = False
        return True

    return False


def crear_alarma(
    hora,
    minuto,
    funcion_aviso,
    *,
    momento=None
):

    if _cierre.is_set():
        return False
    if type(hora) is not int or type(minuto) is not int or not (0 <= hora <= 23 and 0 <= minuto <= 59):
        raise ValueError('Hora de alarma inválida.')
    ahora = datetime.now()
    if momento is None:
        # Compatibilidad con llamadores anteriores: próxima ocurrencia de HH:MM.
        vencimiento = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if vencimiento < ahora.replace(second=0, microsecond=0):
            vencimiento += timedelta(days=1)
    else:
        if not isinstance(momento, _FechaHora):
            raise ValueError('Indica una fecha y hora completas para la alarma.')
        vencimiento = momento.astimezone().replace(tzinfo=None) if momento.tzinfo else momento
        if (vencimiento.hour, vencimiento.minute) != (hora, minuto) or vencimiento <= ahora:
            raise ValueError('La fecha y hora de la alarma ya pasaron o no coinciden con sus parámetros.')
        if (_FechaHora.fromtimestamp(vencimiento.timestamp()) != vencimiento
                or vencimiento.replace(fold=1).timestamp() != vencimiento.timestamp()):
            raise ValueError('La hora local es ambigua o inexistente por cambio de horario.')

    def vigilar_alarma():

        imprimir_seguro(
            f"⏰ Alarma programada para "
            f"{vencimiento:%d/%m/%Y %H:%M}, hora local"
        )

        while not _cierre.is_set():

            ahora = datetime.now()

            if ahora >= vencimiento:

                funcion_aviso(
                    "La alarma está sonando."
                )

                sonar_alarma()

                break

            _cierre.wait(1)

    hilo = threading.Thread(
        target=vigilar_alarma,
        daemon=True
    )

    hilo.start()
    return True


def cerrar_alarmas():
    """Cancelar vigilantes y sonido al cerrar EVA, sin esperar en Tkinter."""
    _cierre.set()
    detener_alarma()
