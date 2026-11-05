"""Alias locales explícitos; NO guarda código ejecutable ni acciones libres."""
from __future__ import annotations

from pathlib import Path

from persistencia import AlmacenJSON, ErrorPersistencia, bloquear, ruta_local

from .texto import normalizar

INTENCIONES_AUTORIZABLES = frozenset({
    'consultar_hora', 'consultar_fecha', 'crear_recordatorio',
    'consultar_recordatorios', 'crear_alarma', 'detener_alarma',
    'abrir_aplicacion', 'cerrar_aplicacion', 'spotify_reproducir',
    'spotify_pausar', 'ayuda',
})


def ruta_alias() -> Path:
    return ruta_local('inteligencia_local/alias_comandos.json')


def _validar(datos):
    valido = isinstance(datos, dict) and all(
        isinstance(k, str) and isinstance(v, str) and v in INTENCIONES_AUTORIZABLES
        for k, v in datos.items())
    return (dict(datos), True) if valido else ({}, False)


_almacen = AlmacenJSON('alias_comandos.json', _validar, dict)


def cargar_alias(ruta: Path | None = None) -> dict[str, str]:
    ruta = Path(ruta) if ruta else ruta_alias()
    try:
        with bloquear(ruta):
            return _almacen.leer(ruta)
    except OSError:
        raise ErrorPersistencia('No se pudieron leer los alias personales. Revisa los permisos.') from None


def registrar_alias(frase: str, intencion: str, ruta: Path | None = None, *, confirmado=False) -> Path:
    """API heredada: requiere confirmación. Preferir ComandosPersonales.proponer.

    Conserva el formato antiguo; esos alias sólo asignan intenciones sin parámetros
    y no se importan automáticamente al nuevo intérprete.
    """
    if confirmado is not True:
        raise ValueError('Se requiere confirmación explícita antes de guardar un alias.')
    if intencion not in INTENCIONES_AUTORIZABLES:
        raise ValueError('Intención no autorizada para alias')
    clave = normalizar(frase)
    if len(clave) < 5 or len(clave) > 180:
        raise ValueError('La frase debe tener entre 5 y 180 caracteres')
    destino = Path(ruta) if ruta else ruta_alias()
    try:
        with bloquear(destino):
            actual = _almacen.leer(destino)
            if clave in actual and actual[clave] != intencion:
                raise ValueError('La frase ya está asociada a otra intención')
            actual[clave] = intencion
            _almacen.guardar(destino, actual)
    except OSError:
        raise ErrorPersistencia('No se guardó el alias. Revisa permisos y espacio; el archivo anterior se conserva.') from None
    return destino
