"""Enseñanza explícita con confirmación, sin ejecución ni aprendizaje implícito."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import re
import secrets
import threading
import time

from persistencia import AlmacenJSON, ErrorPersistencia, bloquear, ruta_local
from .texto import normalizar
from .parametros import extraer_parametros
from .seguridad import INTENCIONES, revisar_seguridad


def validar_asociaciones(datos):
    if not isinstance(datos, dict) or len(datos) > 1000:
        return {}, False
    for frase, valor in datos.items():
        if (not isinstance(frase, str) or not 5 <= len(frase) <= 180 or normalizar(frase) != frase
                or revisar_seguridad(frase) or not isinstance(valor, dict)
                or set(valor) != {'intencion', 'orden'}
                or not isinstance(valor['intencion'], str) or valor['intencion'] not in INTENCIONES
                or not isinstance(valor['orden'], str) or revisar_seguridad(valor['orden'])
                or intencion_explicita(valor['orden']) != valor['intencion']):
            return {}, False
    return deepcopy(datos), True


def intencion_explicita(orden):
    """La enseñanza no confía en una predicción estadística para elegir la acción."""
    t = normalizar(orden)
    patrones = (
        (r'^abre\b', 'abrir_aplicacion'), (r'^cierra\b', 'cerrar_aplicacion'),
        (r'^(?:recuerdame|avisame|crea un recordatorio)\b', 'crear_recordatorio'),
        (r'^(?:crea|pon|programa) una alarma\b', 'crear_alarma'),
        (r'^(?:deten|para|silencia) la alarma$', 'detener_alarma'),
        (r'^(?:pausa la musica|pausa spotify)$', 'spotify_pausar'),
        (r'^(?:reproduce|pon|reanuda|continua|siguiente|anterior)\b', 'spotify_reproducir'),
        (r'^(?:dime la hora|que hora es)$', 'consultar_hora'),
        (r'^(?:dime la fecha|que fecha es)$', 'consultar_fecha'),
        (r'^(?:consulta|muestra) (?:mis |los )?recordatorios$', 'consultar_recordatorios'),
        (r'^(?:ayuda|muestra la ayuda)$', 'ayuda'),
    )
    return next((intencion for patron, intencion in patrones if re.search(patron, t)), None)


class ComandosPersonales:
    def __init__(self, ruta=None, reloj=time.monotonic):
        self.ruta = Path(ruta) if ruta is not None else None
        self.almacen = AlmacenJSON('comandos_personales.json', validar_asociaciones, dict)
        self.reloj = reloj
        self.pendientes = {}
        self.cerrojo = threading.RLock()

    @contextmanager
    def transaccion(self):
        destino = self.ruta if self.ruta is not None else ruta_local('inteligencia_local/comandos_personales.json')
        try:
            with bloquear(destino):
                yield destino
        except OSError:
            raise ErrorPersistencia('No se pudieron guardar o leer los comandos personales. '
                                   'Revisa permisos y espacio disponible; se conserva el archivo anterior.') from None

    def consultar(self):
        with self.transaccion() as ruta:
            return self.almacen.leer(ruta)

    def proponer(self, frase, orden=None, ahora=None):
        if orden is None:
            m = re.fullmatch(r'\s*cuando diga\s+(.+?),\s*(.+?)\s*', frase, re.I)
            if not m:
                raise ValueError('Usa: Cuando diga modo estudio, abre la calculadora.')
            frase, orden = m.groups()
        clave = normalizar(frase)
        intencion = intencion_explicita(orden)
        valor = {'intencion': intencion, 'orden': orden}
        if not validar_asociaciones({clave: valor})[1]:
            raise ValueError('La expresión o la acción no están autorizadas. Usa una orden local explícita.')
        propuesta = extraer_parametros(intencion, orden, ahora)
        if propuesta['estado'] != 'propuesta':
            raise ValueError(propuesta['pregunta'])
        actual = self.consultar()
        if clave in actual and actual[clave] != valor:
            raise ValueError('La expresión ya tiene otra asociación. Elimínala explícitamente antes de cambiarla.')
        return self._pendiente('guardar', clave, valor)

    def proponer_eliminacion(self, frase):
        clave = normalizar(frase)
        actual = self.consultar()
        if clave not in actual:
            raise ValueError('No existe esa expresión personal.')
        return self._pendiente('eliminar', clave, actual[clave])

    def _pendiente(self, operacion, clave, valor):
        with self.cerrojo:
            ahora = self.reloj()
            self.pendientes = {k: v for k, v in self.pendientes.items() if v['vence'] > ahora}
            if len(self.pendientes) >= 100:
                raise ValueError('Hay demasiadas confirmaciones pendientes; resuélvelas primero.')
            token = secrets.token_urlsafe(18)
            self.pendientes[token] = dict(operacion=operacion, frase=clave, valor=deepcopy(valor), vence=ahora + 300)
        return {'estado': 'confirmacion', 'token': token, 'operacion': operacion,
                'frase': clave, 'accion': deepcopy(valor), 'ejecutable': False,
                'pregunta': f'¿Confirmas {operacion} la asociación «{clave}» con «{valor["orden"]}»?'}

    def confirmar(self, token, aceptado=False):
        with self.cerrojo:
            pendiente = self.pendientes.get(token)
            if pendiente is None or pendiente['vence'] <= self.reloj():
                self.pendientes.pop(token, None)
                raise ValueError('Confirmación desconocida o vencida. Vuelve a proponerla.')
            if aceptado is not True:
                self.pendientes.pop(token)
                return False
            with self.transaccion() as ruta:
                datos = self.almacen.leer(ruta)
                clave, valor = pendiente['frase'], pendiente['valor']
                if clave in datos and datos[clave] != valor:
                    raise ValueError('La asociación cambió mientras confirmabas. Consulta y vuelve a intentarlo.')
                if pendiente['operacion'] == 'guardar':
                    datos[clave] = deepcopy(valor)
                else:
                    datos.pop(clave, None)
                self.almacen.guardar(ruta, datos)
            self.pendientes.pop(token)  # Sólo consumir después del guardado confirmado.
            return True

    def interpretar(self, frase, ahora=None):
        if revisar_seguridad(frase):
            return None
        valor = self.consultar().get(normalizar(frase))
        if valor is None:
            return None
        # Fechas relativas se interpretan en cada uso; fechas pasadas piden aclaración.
        resultado = extraer_parametros(valor['intencion'], valor['orden'], ahora)
        resultado['origen'] = 'personal_confirmado'
        return resultado
