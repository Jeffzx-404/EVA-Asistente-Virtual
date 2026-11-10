"""Propuestas en memoria: validar y aclarar, sin escribir ni recibir ejecutores."""
from datetime import datetime
import re

from comandos_voz import preparar_comando, normalizar_intencion
from ordenes_compuestas import detectar_compuesta
from .contexto import analizar_contexto, validar_contexto
from .parametros import validar_accion, _momento
from .seguridad import revisar_seguridad


def validar_propuesta(parametros, ahora):
    datos = validar_accion('crear_recordatorio', parametros)
    momento = datetime.strptime(datos['fecha'], '%Y-%m-%d').replace(
        hour=datos['hora'], minute=datos['minuto'])
    if momento <= ahora:
        raise ValueError('La fecha y hora ya pasaron. Repite el recordatorio completo.')
    if (datetime.fromtimestamp(momento.timestamp()) != momento
            or momento.replace(fold=1).timestamp() != momento.timestamp()):
        raise ValueError('La hora local es ambigua o inexistente. Indica otra.')
    return datos


def _normalizar_peticion(texto, ahora):
    """Adaptar una petición explícita al prefijo que ya entiende el extractor.

    No se cambia el texto clasificado ni se rescatan predicciones rechazadas.
    Si hay contenido entre «necesito que» y «me avises/recuerdes», debe ser
    exclusivamente temporal; no convertir palabras desconocidas en una tarea.
    """
    original = preparar_comando(texto)
    peticion = re.fullmatch(r'(?:por favor\s+)?(?:necesito|quiero)\s+que\s+'
                           r'(.*?)\bme\s+(?:avises|recuerdes)\b(.*)', original)
    if not peticion:
        return original
    antes, asunto = peticion[1].strip(), peticion[2].strip()
    if antes:
        temporal_completo = False
        # Reutilizar el parser y sus tramos, sin duplicar reglas de fecha/hora.
        # Las variantes sólo permiten reconocer la sintaxis AM/PM ambigua;
        # jamás se incorporan a la solicitud ni eligen una hora para el usuario.
        for periodo in ('', ' de la mañana', ' de la tarde'):
            temporal = antes + periodo
            try:
                _, tramos = _momento(temporal, ahora)
            except (ValueError, OverflowError, OSError):
                continue
            for inicio, fin in sorted(tramos, reverse=True):
                temporal = temporal[:inicio] + ' ' + temporal[fin:]
            if normalizar_intencion(temporal) in ('', 'el', 'para', 'para el'):
                temporal_completo = True
                break
        if not temporal_completo:
            return original
    # La hora al final permite reutilizar también las aclaraciones AM/PM del
    # extractor, que agregan el período a la solicitud todavía incompleta.
    return 'avísame ' + ' '.join(parte for parte in (asunto, antes) if parte)


def preparar_solicitud(texto, ahora):
    """Reutilizar los extractores existentes; nunca elegir una alternativa AM/PM."""
    from aclaraciones_comandos import preparar_recordatorio
    if (revisar_seguridad(texto) or detectar_compuesta(texto)
            or analizar_contexto(texto, ahora) is not None):
        return None
    texto = _normalizar_peticion(texto, ahora)
    if (analizar_contexto(texto, ahora) is not None
            or validar_contexto(texto, 'crear_recordatorio') is not None):
        return None
    revision = preparar_recordatorio(texto, ahora)
    estado = 'esperando_informacion'
    if revision['estado'] == 'propuesta':
        revision['parametros'] = validar_propuesta(revision['parametros'], ahora)
        estado = 'esperando_confirmacion'
    return dict(tipo='recordatorio_inteligente', estado=estado, texto=preparar_comando(texto),
                base=ahora, revision=revision)


def mensaje_propuesta(datos):
    if datos['estado'] == 'esperando_confirmacion':
        p = datos['revision']['parametros']
        fecha = datetime.strptime(p['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y')
        return (f"¿Confirmas guardar el recordatorio «{p['texto']}» el {fecha} "
                f"a las {p['hora']:02d}:{p['minuto']:02d}, hora local del equipo? "
                'Responde «sí» para guardarlo o «cancelar». Todavía no está guardado.')
    return (datos['revision']['pregunta'] + ' Todavía no guardaré nada. '
            'Puedes responder «fecha: mañana», «hora: 18:00», «de la tarde» o «tarea: estudiar», '
            'según lo que falte. Para corregir datos, di «el recordatorio es: avísame ...» '
            'con la tarea, fecha y hora completas. Puedes cancelar.')


def responder_propuesta(datos, texto, ahora):
    """None significa instrucción independiente: descartar la propuesta anterior.

    Los fragmentos sólo se usan tras una intención de recordatorio aceptada y
    se vuelven a validar. Las fechas relativas conservan el ancla de la petición.
    """
    t = normalizar_intencion(texto)
    original = preparar_comando(texto)
    mensaje = lambda contenido, estado='cancelado': dict(tipo='mensaje', estado=estado, mensaje=contenido)
    if t in ('si', 'si confirmo', 'si confirmar', 'si guarda el recordatorio'):
        if datos['estado'] != 'esperando_confirmacion':
            return dict(tipo='mensaje', estado='esperando_informacion', pendiente=datos,
                        mensaje='Aún faltan datos; «sí» no completa la instrucción. ' + mensaje_propuesta(datos))
        try:
            p = validar_propuesta(datos['revision']['parametros'], ahora)
        except (ValueError, OverflowError, OSError):
            return mensaje('La propuesta ya no es válida. Repite el recordatorio completo.', 'caducado')
        return dict(tipo='recordatorio_confirmado', estado='confirmado', parametros=p)

    reemplazo = re.fullmatch(r'el recordatorio es\s*:\s*(.+)', original)
    fecha = re.fullmatch(r'(?:fecha|la fecha es)\s*:?\s+(.+)', original)
    hora = re.fullmatch(r'(?:hora|la hora es)\s*:?\s+(.+)', original)
    tarea = re.fullmatch(r'(?:tarea|la tarea es)\s*:?\s+(.+)', original)
    periodo = {'de la manana': 'am', 'por la manana': 'am', 'am': 'am',
               'de la tarde': 'pm', 'por la tarde': 'pm', 'de la noche': 'pm', 'pm': 'pm'}.get(t)
    fragmento_temporal = re.fullmatch(r'(?:hoy|mañana|pasado mañana|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|a las? .+)', original)
    if not (reemplazo or fecha or hora or tarea or periodo or fragmento_temporal):
        if t.startswith(('si ', 'no ')):
            return mensaje('La respuesta no confirma inequívocamente el recordatorio. Propuesta cancelada.')
        return None
    if revisar_seguridad(texto) or detectar_compuesta(texto):
        return mensaje('La respuesta no es una aclaración segura. Repite una sola solicitud completa.')

    alternativas = datos['revision'].get('pendiente', {}).get('alternativas', {})
    if periodo and periodo in alternativas:
        try:
            p = validar_propuesta(alternativas[periodo], ahora)
        except (ValueError, OverflowError, OSError):
            return mensaje('Esa fecha y hora ya no son válidas. Repite el recordatorio completo.', 'caducado')
        siguiente = dict(datos, estado='esperando_confirmacion',
                         revision=dict(estado='propuesta', parametros=p))
    else:
        nuevo = datos['texto']
        if reemplazo:
            nuevo = reemplazo[1]
        elif tarea:
            if not datos['revision'].get('pregunta', '').startswith('¿Qué quieres que te recuerde?'):
                return dict(tipo='mensaje', estado=datos['estado'], pendiente=datos,
                    mensaje='Para sustituir la tarea, di «el recordatorio es: avísame ...» con todos los datos.')
            # Prefijos idénticos a los aceptados por el extractor. No analizar fechas aquí.
            nuevo = re.sub(r'^(?:por favor\s+)?(?:recu[eé]rdame|av[ií]same|'
                           r'(?:crea|pon|programa|guarda) (?:un )?recordatorio)\b',
                           lambda m: m[0] + ' ' + tarea[1], nuevo, count=1)
        else:
            fragmento = ('a las ' + hora[1] if hora else fecha[1] if fecha else original)
            nuevo += ' ' + fragmento
        siguiente = preparar_solicitud(nuevo, datos['base'])
        if siguiente is None:
            return mensaje('No puedo completar esa propuesta con seguridad. Repite una sola solicitud completa.')
        if siguiente['estado'] == 'esperando_confirmacion':
            try:
                validar_propuesta(siguiente['revision']['parametros'], ahora)
            except (ValueError, OverflowError, OSError):
                return mensaje('La fecha y hora ya pasaron. Repite el recordatorio completo.', 'caducado')
    return dict(tipo='mensaje', estado=siguiente['estado'], pendiente=siguiente,
                mensaje=mensaje_propuesta(siguiente))
