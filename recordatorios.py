"""Recordatorios persistentes: cada modificación es una transacción completa."""

from datetime import datetime
import threading
import time
from uuid import uuid4

from persistencia import (AlmacenJSON, ErrorPersistencia, avisar,
                         exclusion_no_bloqueante, ruta_local)


def validar_recordatorios(datos):
    if not isinstance(datos, list):
        return [], False
    identidades = set()
    for recordatorio in datos:
        if not isinstance(recordatorio, dict):
            return [], False
        if not isinstance(recordatorio.get("texto"), str):
            return [], False
        if "id_aviso" in recordatorio:
            identidad = recordatorio["id_aviso"]
            if (not isinstance(identidad, str) or not identidad
                    or len(identidad) > 128 or identidad in identidades):
                return [], False
            identidades.add(identidad)
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
_cierre = threading.Event()
_revision = threading.Lock()


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

    Un guardia independiente serializa notificadores, nunca escritores. El
    callback se ejecuta SIN transacción; la confirmación relee el almacén y
    retira sólo la misma identidad y contenido. Un cierre entre aviso y guardado
    puede repetir el aviso al reiniciar: no se promete entrega exactamente una vez.
    """
    ahora = ahora or datetime.now()
    if not _revision.acquire(blocking=False):
        return True  # Otro vigilante ya está atendiendo; no esperar ni duplicar.
    try:
        ruta_guardia = ruta_local("recordatorios.json.avisos.lock")
        with exclusion_no_bloqueante(ruta_guardia) as adquirido:
            if not adquirido:
                return True
            return _entregar_vencidos(funcion_aviso, ahora)
    except ErrorPersistencia as error:
        avisar(str(error))
        return False
    finally:
        _revision.release()


def _entregar_vencidos(funcion_aviso, ahora):
    todos_entregados = True
    with _almacen.transaccion() as ruta:
        recordatorios = _almacen.leer(ruta)
        vencidos = []
        identificados = False
        for recordatorio in recordatorios:
            vencimiento = datetime.strptime(recordatorio["fecha"], "%Y-%m-%d").replace(
                hour=recordatorio["hora"], minute=recordatorio["minuto"])
            if vencimiento <= ahora:
                # Identidad estable, no una marca de entrega. Compatible con
                # archivos antiguos y con dos recordatorios de igual contenido.
                if "id_aviso" not in recordatorio:
                    recordatorio["id_aviso"] = uuid4().hex
                    identificados = True
                vencidos.append(recordatorio.copy())
        if identificados:
            _almacen.guardar(ruta, recordatorios)

    for recordatorio in vencidos:
        if _cierre.is_set():
            return False
        # Puede haberse cancelado/modificado mientras se atendía otro aviso.
        with _almacen.transaccion() as ruta:
            if recordatorio not in _almacen.leer(ruta):
                continue
        if not recordatorio.get("completado", False):
            try:
                entregado = funcion_aviso("Recordatorio. " + recordatorio["texto"])
            except Exception:
                entregado = False
            if entregado is not True:
                todos_entregados = False
                avisar("No se pudo confirmar un aviso de recordatorio. "
                       "Se conserva pendiente y se reintentará en 30 segundos.")
                continue
        if _cierre.is_set():
            return False
        with _almacen.transaccion() as ruta:
            actuales = _almacen.leer(ruta)
            if recordatorio in actuales:
                actuales.remove(recordatorio)
                _almacen.guardar(ruta, actuales)
    return todos_entregados


def iniciar_recordatorios(funcion_aviso):
    if _cierre.is_set():
        return None

    def avisar_si_abierto(texto):
        return False if _cierre.is_set() else funcion_aviso(texto)

    def vigilar():
        while not _cierre.is_set():
            try:
                correcto = revisar_recordatorios(avisar_si_abierto)
            except Exception:
                correcto = False
                avisar("No se pudieron revisar los recordatorios. Se conservan "
                       "los datos y se reintentará en 30 segundos.")
            # Evitar una sucesión de avisos ante fallos persistentes. Al arrancar
            # se revisa inmediatamente, incluyendo todos los atrasados.
            _cierre.wait(5 if correcto else 30)

    hilo = threading.Thread(target=vigilar, daemon=True)
    hilo.start()
    return hilo


def cerrar_recordatorios():
    """Detener próximas revisiones; una transacción ya iniciada conserva su atomicidad."""
    _cierre.set()


def eliminar_todos_recordatorios():
    return guardar_recordatorios([])
