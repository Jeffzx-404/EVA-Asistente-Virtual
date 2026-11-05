"""Extracción conservadora en español. Devuelve datos, jamás funciones ejecutables."""
from datetime import datetime, timedelta
import re
from tiempo_eva import convertir_numero, interpretar_hora
from .texto import normalizar
from .seguridad import INTENCIONES, APLICACIONES, revisar_seguridad

DIAS = ('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')
MESES = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre')


def numero(texto):
    texto = normalizar(texto)
    valor = convertir_numero(texto)
    if valor is not None:
        return valor
    decenas = {'treinta': 30, 'cuarenta': 40, 'cincuenta': 50, 'sesenta': 60,
               'setenta': 70, 'ochenta': 80, 'noventa': 90}
    partes = texto.split(' y ')
    if partes[0] in decenas:
        unidad = convertir_numero(partes[1]) if len(partes) == 2 else 0
        if unidad is not None and 0 <= unidad < 10:
            return decenas[partes[0]] + unidad
    return None


def _momento(texto, ahora):
    # El texto usado aquí conserva ':' y separadores de fecha.
    t = texto.casefold()
    t = t.translate(str.maketrans('áéíóúñ', 'aeioun'))
    relativos = list(re.finditer(r'\b(?:en|dentro de) (media hora|una hora y media|'
                         r'(?:\d+|[a-z]+(?: y [a-z]+)?) (?:minutos?|horas?|dias?))\b', t))
    relativo = relativos[0] if relativos else None
    if relativo:
        resto = t[:relativo.start()] + t[relativo.end():]
        if len(relativos) != 1 or re.search(r'\b(?:hoy|manana|a las|a la)\b|\d{1,4}[-/]\d', resto):
            raise ValueError('Indica una sola duración o una fecha y hora, sin combinarlas.')
        valor = relativo.group(1)
        if valor == 'media hora':
            minutos = 30
        elif valor == 'una hora y media':
            minutos = 90
        else:
            cantidad, unidad = valor.rsplit(' ', 1)
            cantidad = numero(cantidad)
            if cantidad is None or cantidad <= 0:
                raise ValueError('Indica una duración positiva y concreta.')
            minutos = cantidad * (1440 if unidad.startswith('dia') else 60 if unidad.startswith('hora') else 1)
        if minutos > 525600:
            raise ValueError('Indica una duración de hasta un año.')
        destino = ahora + timedelta(minutes=minutos)
        if destino.second or destino.microsecond:
            destino += timedelta(minutes=1)  # Almacenamiento por minuto: nunca avisar antes.
        return destino.replace(second=0, microsecond=0), [relativo.span()]

    fechas = []
    for patron, formato in ((r'\b\d{4}-\d{2}-\d{2}\b', '%Y-%m-%d'),
                            (r'\b\d{1,2}/\d{1,2}/\d{4}\b', '%d/%m/%Y')):
        for m in re.finditer(patron, t):
            fechas.append((datetime.strptime(m.group(), formato).date(), m.span()))
    for m in re.finditer(r'\b(\d{1,2}) de (' + '|'.join(MESES) + r') de (\d{4})\b', t):
        fechas.append((datetime(int(m[3]), MESES.index(m[2]) + 1, int(m[1])).date(), m.span()))
    for m in re.finditer(r'\b(pasado manana|manana|hoy)\b', t):
        if t[max(0, m.start()-6):m.start()].endswith('de la '):
            continue
        dias = {'hoy': 0, 'manana': 1, 'pasado manana': 2}[m.group()]
        fechas.append(((ahora + timedelta(days=dias)).date(), m.span()))
    for m in re.finditer(r'\b(?:el )?(?:(proximo|este) )?(' + '|'.join(DIAS) + r')\b', t):
        delta = (DIAS.index(m[2]) - ahora.weekday()) % 7
        if delta == 0:
            raise ValueError('Ese día también es hoy. Indica hoy o una fecha exacta.')
        fechas.append(((ahora + timedelta(days=delta)).date(), m.span()))
    if len(fechas) != 1:
        raise ValueError('Indica una sola fecha completa: hoy, mañana o día/mes/año.')
    patron_hora = (r'\b(?:a las|a la)\s+(\d{1,2}:\d{2}|\d{1,2}|[a-z]+(?: y (?:media|cuarto|[a-z]+))?)'
                  r'(?:\s*(am|pm|de la manana|de la tarde|de la noche))?\b(?![:\d])')
    horas = list(re.finditer(patron_hora, t))
    especiales = list(re.finditer(r'\b(mediodia|medianoche)\b', t))
    if len(horas) + len(especiales) != 1:
        raise ValueError('Indica una hora exacta; por ejemplo a las 18:30.')
    if especiales:
        m = especiales[0]
        hora, minuto = (12 if m[1] == 'mediodia' else 0), 0
    else:
        m = horas[0]
        if re.match(r'(?:\.\d|\s+(?:y|menos)\b)', t[m.end():]):
            raise ValueError('La hora no es inequívoca. Escríbela completa, por ejemplo 18:30.')
        valor, periodo = m[1], m[2]
        if ':' in valor:
            hora, minuto = map(int, valor.split(':'))
        elif ' y ' in valor and valor.split(' y ')[1] not in ('media', 'cuarto'):
            izquierda, derecha = valor.split(' y ')
            hora, minuto = numero(izquierda), numero(derecha)
        else:
            interpretada = interpretar_hora(valor)
            if interpretada is None:
                raise ValueError('No pude interpretar la hora.')
            hora, minuto = interpretada
        if hora is None or minuto is None or not (0 <= hora <= 23 and 0 <= minuto <= 59):
            raise ValueError('Hora fuera de rango.')
        if periodo:
            if not 1 <= hora <= 12:
                raise ValueError('No combines horario de 24 horas con mañana/tarde o AM/PM.')
            hora = hora % 12 + (12 if periodo in ('pm', 'de la tarde', 'de la noche') else 0)
        elif ':' not in valor and 1 <= hora <= 12:
            raise ValueError('¿De la mañana o de la tarde? También puedes indicar 18:00.')
    fecha, tramo = fechas[0]
    return datetime.combine(fecha, datetime.min.time()).replace(hour=hora, minute=minuto), [tramo, m.span()]


def validar_accion(intencion, parametros):
    if not isinstance(intencion, str) or intencion not in INTENCIONES or not isinstance(parametros, dict):
        raise ValueError('Acción no autorizada.')
    campos = {'abrir_aplicacion': {'aplicacion'}, 'cerrar_aplicacion': {'aplicacion'},
              'crear_recordatorio': {'texto', 'fecha', 'hora', 'minuto'},
              'crear_alarma': {'fecha', 'hora', 'minuto'},
              'spotify_reproducir': {'accion', 'consulta'}, 'spotify_pausar': {'accion'}}
    if set(parametros) != campos.get(intencion, set()):
        raise ValueError('Faltan parámetros o existen campos no permitidos.')
    if 'aplicacion' in parametros and (not isinstance(parametros['aplicacion'], str)
                                     or parametros['aplicacion'] not in APLICACIONES):
        raise ValueError('Aplicación no autorizada.')
    if 'fecha' in parametros:
        if not isinstance(parametros['fecha'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', parametros['fecha']):
            raise ValueError('Fecha inválida.')
        datetime.strptime(parametros['fecha'], '%Y-%m-%d')
        if (type(parametros['hora']) is not int or not 0 <= parametros['hora'] <= 23
                or type(parametros['minuto']) is not int or not 0 <= parametros['minuto'] <= 59):
            raise ValueError('Hora inválida.')
    for clave in ('texto', 'consulta'):
        if clave in parametros and (not isinstance(parametros[clave], str)
                or len(parametros[clave]) > 300 or (parametros[clave] and not parametros[clave].isprintable())
                or (clave == 'texto' and not parametros[clave].strip())):
            raise ValueError('Descripción inválida.')
    if intencion == 'spotify_pausar' and parametros['accion'] != 'pausar':
        raise ValueError('Acción musical no autorizada.')
    if intencion == 'spotify_reproducir':
        if parametros['accion'] not in ('reproducir_cancion', 'continuar', 'siguiente', 'anterior'):
            raise ValueError('Acción musical no autorizada.')
        if (parametros['accion'] == 'reproducir_cancion') != bool(parametros['consulta'].strip()):
            raise ValueError('Indica una canción concreta o pide continuar.')
    return dict(parametros)


def extraer_parametros(intencion, texto, ahora=None):
    ahora = ahora or datetime.now()  # Reloj local de Windows; nunca UTC implícito.
    if ahora.tzinfo is not None:
        ahora = ahora.astimezone().replace(tzinfo=None)
    problema = revisar_seguridad(texto)
    if problema:
        return {'estado': 'aclaracion', 'pregunta': problema, 'ejecutable': False}
    t = normalizar(texto)
    try:
        datos = {}
        if intencion in ('abrir_aplicacion', 'cerrar_aplicacion'):
            aplicaciones = [nombre for nombre, alias in APLICACIONES.items()
                            if any(re.search(r'\b' + re.escape(a) + r'\b', t) for a in alias)]
            if len(aplicaciones) != 1:
                raise ValueError('Indica una aplicación autorizada: ' + ', '.join(APLICACIONES) + '.')
            if re.search(r'\b(?:todos|todas|cuenta|archivo|documento)\b', t) and aplicaciones != ['explorador']:
                raise ValueError('Indica solamente el nombre de la aplicación.')
            datos = {'aplicacion': aplicaciones[0]}
        elif intencion in ('crear_recordatorio', 'crear_alarma'):
            if re.search(r'\b(?:cada|diariamente|semanalmente|hasta|aproximadamente|entre|antes|despues|unos|o)\b', t):
                raise ValueError('Indica una sola fecha y hora; no se admiten recurrencias.')
            momento, tramos = _momento(texto, ahora)
            if momento <= ahora:
                raise ValueError('La fecha y hora ya pasaron. Indica otra.')
            if (datetime.fromtimestamp(momento.timestamp()) != momento
                    or momento.replace(fold=1).timestamp() != momento.timestamp()):
                raise ValueError('La hora local es ambigua o inexistente por cambio de horario.')
            datos = {'fecha': momento.strftime('%Y-%m-%d'), 'hora': momento.hour, 'minuto': momento.minute}
            if intencion == 'crear_recordatorio':
                descripcion = texto
                for inicio, fin in sorted(tramos, reverse=True):
                    descripcion = descripcion[:inicio] + ' ' + descripcion[fin:]
                descripcion = re.sub(r'^\s*(?:oye\s+)?eva[\s,:]*', '', descripcion, flags=re.I)
                descripcion, prefijos = re.subn(r'^\s*(?:por favor\s+)?(?:recu[eé]rdame|av[ií]same|'
                    r'(?:necesito|quiero) que me (?:avises|recuerdes)|'
                    r'(?:crea|pon|programa|guarda) (?:un )?recordatorio)\b', '', descripcion, flags=re.I)
                if prefijos != 1:
                    raise ValueError('Indica el asunto con «recuérdame ...» o «avísame ...».')
                descripcion = re.sub(r'^\s*(?:que|para|de)\b\s*', '', descripcion, flags=re.I)
                descripcion = re.sub(r'\b(?:para|el|al|a las|a la)\s*$', '', descripcion, flags=re.I)
                descripcion = ' '.join(descripcion.strip(' ,.;').split())
                if not descripcion or normalizar(descripcion) in ('un aviso', 'recordatorio', 'algo'):
                    raise ValueError('¿Qué quieres que te recuerde?')
                datos['texto'] = descripcion
        elif intencion == 'spotify_pausar':
            datos = {'accion': 'pausar'}
        elif intencion == 'spotify_reproducir':
            if re.search(r'\b(?:playlist|lista|album)\b', t):
                raise ValueError('Indica una canción concreta; las listas y álbumes no están preparados.')
            accion = next((a for patron, a in ((r'\b(?:continua|reanuda|play)\b', 'continuar'),
                          (r'\b(?:siguiente|salta)\b', 'siguiente'),
                          (r'\b(?:anterior|retrocede)\b', 'anterior')) if re.search(patron, t)), None)
            consulta = ''
            if accion is None:
                m = re.fullmatch(r'(?:reproduce|pon|quiero escuchar|escuchar)\s+(?:la canci[oó]n\s+)?(.+)', texto.strip(), re.I)
                consulta = re.sub(r'\s+en spotify$', '', m[1], flags=re.I).strip() if m else ''
                if not consulta or normalizar(consulta) in ('musica', 'una cancion', 'mi musica', 'spotify'):
                    raise ValueError('¿Qué canción quieres escuchar? También puedes pedir continuar.')
                accion = 'reproducir_cancion'
            datos = {'accion': accion, 'consulta': consulta}
        elif intencion == 'consultar_hora' and re.search(r'\b(?:en|de) (?:tokio|madrid|otro|otra|japon)\b', t):
            raise ValueError('Sólo está preparada la hora local del equipo.')
        datos = validar_accion(intencion, datos)
        return {'estado': 'propuesta', 'intencion': intencion, 'parametros': datos, 'ejecutable': False}
    except (ValueError, OverflowError, OSError) as error:
        return {'estado': 'aclaracion', 'pregunta': str(error), 'ejecutable': False}
