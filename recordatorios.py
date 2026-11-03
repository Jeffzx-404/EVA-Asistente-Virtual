"""Recordatorios persistentes: cada modificación es una transacción completa."""

from datetime import datetime
import threading
import time

from persistencia import AlmacenJSON, ErrorPersistencia, avisar


def validar_recordatorios(datos):
    if not isinstance(datos, list):
        return [], False
    for recordatorio in datos:
        if not isinstance(recordatorio, dict):
            return [], False
        if not isinstance(recordatorio.get("texto"), str):
            return [], False
        fecha = recordatorio.get("fecha")
        try:
            if not isinstance(fecha, str) or datetime.strptime(
                fecha, "%Y-%m-%d"
            ).strftime("%Y-%m-%d") != fecha:
                return [], False
        except ValueError:
            return [], False
        if (type(recordatorio.get("hora")) is not int
                or not 0 <= recordatorio["hora"] <= 23
                or type(recordatorio.get("minuto")) is not int
                or not 0 <= recordatorio["minuto"] <= 59
                or type(recordatorio.get("completado", False)) is not bool):
            return [], False
    return datos, True


_almacen = AlmacenJSON("recordatorios.json", validar_recordatorios, list)


def cargar_recordatorios():
    try:
        with _almacen.transaccion() as ruta:
            return _almacen.leer(ruta)
    except ErrorPersistencia as error:
        avisar(str(error))
        # None distingue el error de una lista realmente vacía.
        return None


def guardar_recordatorios(recordatorios):
    """Reemplazo explícito. Para agregar o completar, usar las transacciones abajo."""
    try:
        with _almacen.transaccion() as ruta:
            _almacen.leer(ruta)  # Nunca reemplazar un archivo ilegible o dañado.
            _almacen.guardar(ruta, recordatorios)
        return True
    except ErrorPersistencia as error:
        avisar(str(error))
        return False


def crear_recordatorio(texto, fecha, hora, minuto):
    try:
        with _almacen.transaccion() as ruta:
            recordatorios = _almacen.leer(ruta)
            recordatorios.append({
                "texto": texto, "fecha": fecha, "hora": hora,
                "minuto": minuto, "completado": False,
            })
            _almacen.guardar(ruta, recordatorios)
        return True
    except ErrorPersistencia as error:
        avisar(str(error))
        return False


def obtener_recordatorios_pendientes():
    recordatorios = cargar_recordatorios()
    if recordatorios is None:
        return None
    return [r for r in recordatorios if not r.get("completado", False)]


def revisar_recordatorios(funcion_aviso, ahora=None):
    """Avisar vencidos y eliminarlos sólo con confirmación explícita (True).

    El callback se ejecuta en el vigilante, nunca en el hilo Tk. Mantener la
    transacción evita que dos vigilantes entreguen el mismo aviso. El callback
    no debe volver a acceder al almacén ni esperar a otro hilo que lo haga.
    Si el proceso termina entre aviso y guardado, el aviso puede repetirse:
    se prefiere esa repetición a perder un recordatorio pendiente.
    """
    ahora = ahora or datetime.now()
    todos_entregados = True
    try:
        with _almacen.transaccion() as ruta:
            recordatorios = _almacen.leer(ruta)
            indice = 0
            while indice < len(recordatorios):
                recordatorio = recordatorios[indice]
                vencimiento = datetime.strptime(recordatorio["fecha"], "%Y-%m-%d").replace(
                    hour=recordatorio["hora"], minute=recordatorio["minuto"]
                )
                if vencimiento > ahora:
                    indice += 1
                    continue
                # Compatibilidad: los completados de versiones anteriores ya
                # fueron atendidos. Limpiarlos sin volver a anunciarlos.
                if not recordatorio.get("completado", False):
                    try:
                        entregado = funcion_aviso("Recordatorio. " + recordatorio["texto"])
                    except Exception:
                        entregado = False
                    if entregado is not True:
                        todos_entregados = False
                        avisar("No se pudo confirmar un aviso de recordatorio. "
                               "Se conserva pendiente y se reintentará en 30 segundos.")
                        indice += 1
                        continue
                restantes = recordatorios[:indice] + recordatorios[indice + 1:]
                # Un guardado por aviso: un fallo posterior no resucita los
                # anteriores. No avanzar si la escritura no se confirmó.
                _almacen.guardar(ruta, restantes)
                recordatorios = restantes
        return todos_entregados
    except ErrorPersistencia as error:
        avisar(str(error))
        return False


def iniciar_recordatorios(funcion_aviso):
    def vigilar():
        while True:
            try:
                correcto = revisar_recordatorios(funcion_aviso)
            except Exception:
                correcto = False
                avisar("No se pudieron revisar los recordatorios. Se conservan "
                       "los datos y se reintentará en 30 segundos.")
            # Evitar una sucesión de avisos ante fallos persistentes. Al arrancar
            # se revisa inmediatamente, incluyendo todos los atrasados.
            time.sleep(5 if correcto else 30)

    hilo = threading.Thread(target=vigilar, daemon=True)
    hilo.start()


def eliminar_todos_recordatorios():
    return guardar_recordatorios([])
