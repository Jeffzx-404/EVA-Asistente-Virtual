"""Contratos contextuales conservadores; no clasifican fechas ni ejecutan acciones.

Una coincidencia léxica sólo identifica posibilidades para diagnóstico. El modelo,
sus umbrales y el extractor existente siguen siendo necesarios para una propuesta.
"""
import re
from .texto import normalizar
from .parametros import extraer_parametros
from .seguridad import APLICACIONES

ABRIR = r'\b(?:abre(?:me)?|abrir|abras|inicia|iniciar|inicies|arranca|lanza|ejecuta|abr[ae]s)\b'
CERRAR = r'\b(?:cierra|cierres|cerrar|cierr[ae]s|finaliza|termina|sal de)\b'
RECORDAR = r'\b(?:recuerdame|avisame|recordarme|avisarme|recordar|recordatorio)\b'
CREAR = r'\b(?:pon|ponme|poner|crea|crear|programa|programar|configura|activa|fija|prepara)\b'
DETENER = r'\b(?:deten|detener|detienes|para|parar|silencia|silenciar|apaga|par[ae]s|callar)\b'
PAUSAR = r'\b(?:pausa|pausar|pauses|interrumpe|interrumpir|paus[ae]s)\b'
MUSICA = r'\b(?:musica|cancion|canciones|pista|reproduccion|spotify)\b'
REPRODUCIR = r'\b(?:reproduce|reproducir|pon|escuchar|reanuda|continua|siguiente|anterior|play)\b'
INICIO_ORDEN = (r'(?:abre\w*|abrir|inicia\w*|iniciar|cierra\w*|cerrar|pon\w*|'
                r'pausa\w*|reproduce\w*|reanuda\w*|deten\w*|detien\w*|silencia\w*|'
                r'recuerdame|avisame|programa\w*|crea\w*|dime|consulta\w*|'
                r'muestra\w*|enciende\w*|apaga\w*|envia\w*|borra\w*|'
                r'elimina\w*|busca\w*|descarga\w*|ejecuta\w*|cambia\w*|explica\w*|redacta\w*|escribe\w*|traduce\w*|calcula\w*|'
                r'que hora|que fecha|cual es|puedes|podrias|necesito|quiero)')


def posibilidades(texto):
    t = normalizar(texto)
    resultado = []
    if re.search(ABRIR, t):
        resultado.append('abrir_aplicacion')
    if re.search(CERRAR, t):
        resultado.append('cerrar_aplicacion')
    if re.search(r'\b(?:alarma|despertador)\b', t):
        if re.search(DETENER, t):
            resultado.append('detener_alarma')
        if re.search(CREAR, t):
            resultado.append('crear_alarma')
    if re.search(RECORDAR, t) and (re.search(CREAR, t) or re.search(r'\b(?:recuerdame|avisame|recordarme|avisarme)\b', t)):
        resultado.append('crear_recordatorio')
    elif re.search(r'\b(?:recordatorios|avisos|pendientes)\b', t):
        resultado.append('consultar_recordatorios')
    if re.search(PAUSAR, t) and re.search(MUSICA, t):
        resultado.append('spotify_pausar')
    elif re.search(REPRODUCIR, t) and (re.search(MUSICA, t) or re.match(r'^(?:reproduce|pon|quiero escuchar)\b', t)):
        if not re.search(r'\b(?:alarma|despertador|recordatorio)\b', t):
            resultado.append('spotify_reproducir')
    if re.search(r'\b(?:hora|reloj)\b', t) and not resultado:
        resultado.append('consultar_hora')
    if re.search(r'\b(?:fecha|dia|mes|ano)\b', t) and not resultado:
        resultado.append('consultar_fecha')
    if re.search(r'\b(?:ayuda|capacidades|funciones|comandos|instrucciones|puedes hacer)\b', t) and not resultado:
        resultado.append('ayuda')
    return resultado


def respuesta(estado, tipo, motivo, solicitudes=None):
    solicitudes = solicitudes or []
    return dict(estado=estado, tipo=tipo, motivo=motivo, pregunta=motivo,
                intenciones_posibles=sorted({i for s in solicitudes for i in s['intenciones_posibles']}),
                solicitudes=solicitudes, por_resolver=[motivo], ejecutable=False)


def analizar_contexto(texto, ahora=None):
    if not isinstance(texto, str) or not texto.strip() or len(texto) > 1000:
        return respuesta('aclaracion', 'entrada_invalida', 'Indica una instrucción breve y concreta.')
    t = normalizar(texto)
    # Separar sólo conectores seguidos de otra petición: no partir «siete y media».
    # Conservar signos de hora/fecha y la descripción original para el extractor.
    plegado = texto.lower().translate(str.maketrans('áéíóúñ', 'aeioun'))
    cortes = list(re.finditer(r'\b(?:y|e|o|ni|luego|despues|ademas|mientras|entonces)\s+(?=(?:no\s+|nunca\s+)?' + INICIO_ORDEN + r'\b)', plegado))
    partes, inicio = [], 0
    for corte in cortes:
        partes.append(texto[inicio:corte.start()].strip())
        inicio = corte.end()
    partes.append(texto[inicio:].strip())
    # Puntuación y órdenes yuxtapuestas también pueden esconder una segunda acción.
    if len(partes) == 1:
        puntuadas = re.split(r'[;.!?]+|,\s*(?=\w)', texto)
        significativas = [p.strip() for p in puntuadas if normalizar(p) not in
                         ('', 'hola', 'eva', 'por favor', 'gracias', 'buenas')]
        if len(significativas) > 1 and any(posibilidades(p) for p in significativas):
            partes = significativas
    if len(partes) == 1 and not re.search(r'\b(?:recuerdame|avisame|recordarme|avisarme)\b', t):
        verbos = list(re.finditer(r'\b(?:abre|cierra|inicia|pausa|reproduce|deten|silencia|borra|envia|apaga)\b', plegado))
        if len(verbos) > 1:
            posiciones = [0] + [v.start() for v in verbos[1:]] + [len(texto)]
            partes = [texto[a:b].strip() for a, b in zip(posiciones, posiciones[1:])]
    # Objetos coordinados con verbo elíptico: «abre Chrome y Paint».
    if len(partes) == 1 and re.search(ABRIR + '|' + CERRAR, t) and not re.search(RECORDAR, t):
        apps = [nombre for nombre, alias in APLICACIONES.items()
                if any(re.search(r'\b' + re.escape(a) + r'\b', t) for a in alias)]
        if len(apps) > 1:
            intencion = 'cerrar_aplicacion' if re.search(CERRAR, t) else 'abrir_aplicacion'
            return respuesta('aclaracion', 'multiples_objetos', 'Indica una sola aplicación; no se ha elegido ninguna.',
                             [dict(fragmento=a, intenciones_posibles=[intencion], ejecutable=False) for a in apps])
    if len(partes) > 1:
        solicitudes = []
        for parte in partes:
            candidatas = posibilidades(parte)
            validaciones = []
            for intencion in candidatas:
                dato = validar_contexto(parte, intencion) or extraer_parametros(intencion, parte, ahora)
                validaciones.append(dict(intencion=intencion, parametros_completos=dato['estado'] == 'propuesta',
                                         pendiente=dato.get('pregunta'), ejecutable=False))
            solicitudes.append(dict(fragmento=parte.strip(), intenciones_posibles=candidatas,
                                     validaciones=validaciones,
                                     por_resolver=([v['pendiente'] for v in validaciones if v['pendiente']]
                                                  if candidatas else ['No se identifica una acción local autorizada.']),
                                     ejecutable=False))
        return respuesta('aclaracion', 'multiple_o_alternativa',
                         'Hay varias solicitudes o alternativas. Elige una sola y confirma sus datos; ninguna parte fue aceptada.', solicitudes)
    if re.search(r'\b(?:no|nunca|jamas|tampoco|ni)\b', t) or re.search(r'\b(?:evita|evites|deja de|sin)\s+(?:abrir|cerrar|poner|pausar|reproducir|iniciar)\b', t):
        return respuesta('aclaracion', 'negacion', 'La instrucción contiene una negación; aclara qué deseas hacer.')
    if re.search(r'\b(?:si|cuando)\b', t):
        return respuesta('aclaracion', 'condicional', 'No se admiten condiciones o eventos. Indica una solicitud concreta.')
    # No sustituir homófonos globalmente: «sierra» también puede ser un nombre.
    aplicaciones = '|'.join(re.escape(a) for aliases in APLICACIONES.values() for a in aliases)
    if re.fullmatch(r'sierra (?:la |el )?(?:' + aplicaciones + r')(?: por favor)?', t):
        return respuesta('aclaracion', 'homofono_sin_confirmar',
                         '¿Querías decir «cierra»? Repite la solicitud con el nombre de la aplicación.',
                         [dict(fragmento=texto, intenciones_posibles=['cerrar_aplicacion'], ejecutable=False)])
    # No hay historial musical: no fabricar un título a partir de una referencia.
    if (re.match(r'^(?:pon|ponme|reproduce|quiero escuchar) (?:la |mi )?musica\b', t)
            and re.search(r'\b(?:igual que|como|de) (?:ayer|antes|la ultima vez|el otro dia)\b', t)
            or re.fullmatch(r'(?:pon|reproduce) (?:lo de ayer|lo que escuche ayer)', t)):
        return respuesta('aclaracion', 'historial_musical_ausente',
                         'No dispongo de ese historial musical. Indica una canción concreta o pide continuar.')
    if re.search(r'\b(?:eso|aquello|lo mismo|lo de siempre|ya sabes|como antes|esa ventana|esa aplicacion|hazlo|ponlo|cierralo|abrelo)\b', t):
        return respuesta('aclaracion', 'referencia_sin_resolver', 'No tengo una referencia inequívoca. Indica la acción y su objeto.')
    # Pregunta informativa no equivale a una orden de abrir, pausar o crear.
    ayuda_local = re.search(r'\b(?:tus (?:funciones|capacidades|comandos)|usar eva|utilizar eva)\b', t)
    if not ayuda_local and re.match(r'^(?:por que|se puede|como (?:se |puedo |puedes )?(?:abrir|cerrar|crear|programar|funciona)|'
                r'quien|que (?:es|significa|opinas)|explica(?:me)?|cuentame)\b', t):
        return respuesta('desconocido', 'pregunta_externa', 'Es una pregunta informativa; no se propone ninguna acción local.')
    return None


def validar_contexto(texto, intencion):
    """Validar el objeto semántico antes de reutilizar el extractor de parámetros."""
    t = normalizar(texto)
    rechazo = None
    if intencion in ('consultar_fecha', 'consultar_hora'):
        t = re.sub(r'\b(?:mi|tu|su) (?:equipo|reloj|computadora|pc|ordenador|sistema)\b', 'el equipo', t)
        # El reloj local no conoce agendas, fechas personales, historia ni otras zonas.
        if re.search(r'\b(?:mi|mis|tu|tus|su|sus|examen|cita|reunion|cumpleanos|nacimiento|'
                     r'pelicula|vuelo|partido|evento|entrega|entrevista|feriado|historia|ocurrio|'
                     r'empieza|comienza|termina|fue|sera|ayer|manana|pasado|proximo)\b', t):
            rechazo = 'La consulta se refiere a una fecha u hora personal, de un evento o distinta de la actual.'
        elif re.search(r'\b(?:en|de) (?!hoy\b|ahora\b|este\b|esta\b|(?:la )?pantalla(?:$| por favor$)|la (?:computadora|pc|semana)\b|windows\b|el (?:equipo|sistema|ordenador|reloj)\b)[a-z]+', t):
            rechazo = 'Sólo se puede consultar la fecha y hora actuales del equipo local.'
        elif not re.search(r'\b(?:hora|reloj)\b' if intencion == 'consultar_hora' else r'\b(?:fecha|dia|mes|ano)\b', t):
            rechazo = 'La frase no identifica una consulta del reloj o calendario actual.'
    elif intencion == 'ayuda':
        capacidades = re.search(r'\b(?:comandos|capacidades|funciones|opciones|instrucciones de uso|'
                                r'como (?:puedo )?(?:usarte|utilizarte|pedirte|usar eva)|'
                                r'que (?:puedes|sabes) (?:hacer|realizar)|asistente)\b', t)
        if not capacidades and t not in ('ayuda', 'ayudame', 'necesito ayuda', 'muestra la ayuda'):
            rechazo = 'La ayuda local describe las capacidades de EVA; no resuelve otros temas.'
        elif re.search(r'\b(?:para|con|sobre)\b', t) and not re.search(r'\b(?:eva|asistente|comandos|tus funciones|tus capacidades)\b', t):
            rechazo = 'La pregunta de ayuda no trata de las capacidades locales de EVA.'
    elif intencion in ('abrir_aplicacion', 'cerrar_aplicacion'):
        accion = ABRIR if intencion == 'abrir_aplicacion' else CERRAR
        if not re.search(accion, t):
            rechazo = 'Mencionar una aplicación no equivale a pedir abrirla o cerrarla.'
        # Una petición usa un objeto de aplicación, no un documento, cuenta o debate.
        if re.search(r'\b(?:cuenta|documento|archivo|debate|expediente|venta)\b', t) and 'explorador' not in t:
            rechazo = 'El objeto solicitado no es una aplicación autorizada.'
    elif intencion == 'detener_alarma':
        fragmentada = re.fullmatch(r'(?:eba )?(?:para|deten|silencia)(?: por favor)? (?:la )?al arma(?: por favor)?', t)
        if not fragmentada and (not re.search(DETENER, t) or not re.search(r'\b(?:alarma|despertador)\b', t)):
            rechazo = 'Falta una solicitud explícita de detener la alarma.'
    elif intencion == 'crear_alarma':
        if not re.search(CREAR, t) or not re.search(r'\b(?:alarma|despertador)\b', t):
            rechazo = 'No se ha pedido crear una alarma.'
    elif intencion == 'crear_recordatorio':
        if not re.search(RECORDAR, t):
            rechazo = 'Falta una petición explícita de recordatorio.'
    elif intencion == 'consultar_recordatorios':
        consulta_singular = re.fullmatch(r'(?:me )?(?:lees|dices|muestras) lo que tengo pendiente de recordar(?: por favor)?', t)
        if not consulta_singular and not re.search(r'\b(?:recordatorios|avisos|pendientes)\b', t):
            rechazo = 'No se ha identificado la consulta de recordatorios guardados.'
    elif intencion == 'spotify_pausar':
        if not re.search(PAUSAR, t) or not re.search(MUSICA, t):
            rechazo = 'No se ha pedido pausar la reproducción musical.'
    elif intencion == 'spotify_reproducir':
        if not re.search(REPRODUCIR, t):
            rechazo = 'No se ha pedido reproducir una canción o continuar música.'
        if re.search(r'\b(?:cualquiera|algo|lo que sea|esa|aquella|la misma)\b', t):
            return respuesta('aclaracion', 'objeto_ambiguo', 'Indica la canción concreta o pide continuar la reproducción.')
    if rechazo:
        return respuesta('desconocido', 'contexto_incompatible', rechazo)
    return None
