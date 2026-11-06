"""Trazas opcionales de interacciones reales, sólo consola y sin texto libre."""
from contextvars import ContextVar
from functools import wraps
import json
import os
import uuid
from comandos_voz import normalizar_intencion

_actual = ContextVar('diagnostico_comandos', default=None)
# Sólo vocabulario estructural público: nunca nombres, títulos, asuntos ni números.
_PUBLICO = frozenset(('eva dime dame me podrias puedes decir dices informa muestra explica explicame '
    'tus funciones comandos disponibles ayuda hora fecha actual hoy que cual es son dia semana '
    'la el los las de del mi equipo reloj windows por favor y e o ni luego despues ademas '
    'no nunca abre abrir cierra cerrar calculadora spotify paint chrome bloc notas explorador '
    'crea crear una un alarma recordatorio pausa musica').split())


def _texto_seguro(texto):
    t = normalizar_intencion(texto)
    if not t or len(t) > 300 or any(p not in _PUBLICO for p in t.split()):
        return '[texto omitido: contenido libre o sensible]'
    return t


def marcar_ruta(ruta, *, intenciones=(), motivo=None, fallback=False):
    traza = _actual.get()
    if traza is None:
        return
    traza['ruta_procesamiento'] = ruta
    if not traza['recorrido'] or traza['recorrido'][-1] != ruta:
        traza['recorrido'].append(ruta)
    traza['intenciones_detectadas'] = sorted(set(traza['intenciones_detectadas']) | set(intenciones))
    if motivo is not None:
        traza['motivo_rechazo'] = motivo
    traza['fallback_consultado'] |= fallback


def ejecutar_accion(nombre, funcion, *args, **kwargs):
    traza = _actual.get()
    if traza is None:
        return funcion(*args, **kwargs)
    evento = {'ejecutor': nombre, 'resultado': 'sin_confirmar'}
    traza['ejecuciones'].append(evento)  # Se entra al ejecutor, no se deduce de la intención.
    try:
        resultado = funcion(*args, **kwargs)
    except Exception:
        # Una excepción podría producirse después del efecto externo.
        # No afirmar que se ejecutaron cero acciones en ese caso.
        evento['error'] = True
        raise
    if nombre in ('abrir_sitio', 'buscar_internet', 'cerrar_aplicacion'):
        return resultado  # Estos ejecutores antiguos no confirman el resultado del SO.
    confirmacion = resultado.get('exito') if isinstance(resultado, dict) else resultado
    if nombre == 'obtener_recordatorios_pendientes' and isinstance(resultado, list):
        confirmacion = True
    if confirmacion is True:
        evento['resultado'] = 'confirmado'
    elif confirmacion is False:
        evento['resultado'] = 'fallo'
    return resultado


def trazar_interaccion(funcion):
    @wraps(funcion)
    def ejecutar(texto, *args, **kwargs):
        if os.environ.get('EVA_DIAGNOSTICO_COMANDOS') != '1':
            return funcion(texto, *args, **kwargs)
        traza = dict(interaccion_id=uuid.uuid4().hex, texto_normalizado=_texto_seguro(texto),
            ruta_procesamiento='entrada', recorrido=[], intenciones_detectadas=[], motivo_rechazo=None,
            fallback_consultado=False, ejecuciones=[])
        token = _actual.set(traza)
        try:
            return funcion(texto, *args, **kwargs)
        except Exception:
            traza['error'] = 'La interacción terminó con una excepción; no se registran detalles privados.'
            raise
        finally:
            _actual.reset(token)
            estados = [e['resultado'] for e in traza['ejecuciones']]
            confirmadas = estados.count('confirmado')
            traza.update(ejecutores_invocados=len(estados), acciones_confirmadas=confirmadas,
                         acciones_fallidas=estados.count('fallo'),
                         errores_ejecutores=sum(bool(e.get('error')) for e in traza['ejecuciones']),
                         acciones_sin_confirmar=estados.count('sin_confirmar'),
                         acciones_ejecutadas=None if 'sin_confirmar' in estados else confirmadas)
            try:
                print('[EVA comandos] ' + json.dumps(traza, ensure_ascii=True), flush=True)
            except Exception:
                pass
    return ejecutar
