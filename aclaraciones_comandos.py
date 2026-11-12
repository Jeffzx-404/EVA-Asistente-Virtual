"""Validación determinista del enrutador tradicional; no carga modelos ni ejecuta.

Reutiliza únicamente funciones puras del análisis contextual y de parámetros.
El seguimiento mantiene una sola aclaración en memoria durante dos minutos.
"""
from copy import deepcopy
from datetime import datetime
import re
import threading
import time

from comandos_voz import preparar_comando, normalizar_intencion
from eva_inteligencia.contexto import analizar_contexto, validar_contexto
from ordenes_compuestas import detectar_compuesta, titulo_literal
from eva_inteligencia.parametros import extraer_parametros, validar_accion


def es_consulta_personal(texto):
    t = normalizar_intencion(texto)
    if not re.match(r'^(?:dime |dame )?(?:que (?:fecha|hora|dia)|cual es (?:la |el |mi |tu |su )?(?:fecha|hora|dia)|'
                    r'(?:la )?fecha de|a que hora|cuando (?:es|sera|tengo|empieza|comienza))\b', t):
        return False
    if not re.search(r'\b(?:mi|mis|tu|tus|su|sus|examen|cita|reunion|cumpleanos|entrevista|evento)\b', t):
        return False
    intencion = 'consultar_hora' if re.search(r'\b(?:hora|reloj)\b', t) else 'consultar_fecha'
    return validar_contexto(texto, intencion) is not None


def preparar_recordatorio(texto, ahora):
    """Validar fecha, hora y descripción completas sin el clasificador.

    Los alias tradicionales de Whisper se normalizan sólo en el prefijo.
    Las alternativas AM/PM se calculan con el mismo extractor y fecha anclada;
    ninguna de ellas se elige ni se guarda sin la respuesta del usuario.
    """
    texto = preparar_comando(texto)
    texto = re.sub(r'^rec(?:u[eé]rdame|[oó]rdame|uerda\s+me)\b[\s,;:]*',
                   'recuérdame ', texto)
    resultado = extraer_parametros('crear_recordatorio', texto, ahora)
    if resultado['estado'] == 'propuesta':
        return resultado
    alternativas = {}
    for periodo, sufijo in (('am', ' de la mañana'), ('pm', ' de la tarde')):
        alternativa = extraer_parametros('crear_recordatorio', texto + sufijo, ahora)
        if alternativa['estado'] == 'propuesta':
            alternativas[periodo] = alternativa['parametros']
    if alternativas:
        resultado['pendiente'] = {'tipo': 'periodo', 'alternativas': alternativas}
        resultado['pregunta'] += ' Responde «de la mañana» o «de la tarde», o repite la instrucción completa. Puedes cancelar.'
    else:
        resultado['pregunta'] += ' Repite el recordatorio completo con su descripción, fecha y hora.'
    return resultado


def aclaracion_musical(texto):
    """No convertir una referencia al historial en un nombre de canción."""
    texto = preparar_comando(texto)
    canonico = re.sub(r'^(?:reproduce|reproducir|ponme|pon|quiero escuchar|quiero o[ií]r|escuchar)\s+',
                      'reproduce ', texto)
    # Un título explícito puede llamarse «Igual que ayer» o «Lo de siempre».
    if re.match(r'^reproduce (?:la )?canci[oó]n\s+\S', canonico):
        return None
    contexto = analizar_contexto(canonico)
    if ((contexto and contexto['tipo'] in ('historial_musical_ausente', 'referencia_sin_resolver'))
            or normalizar_intencion(canonico) in ('reproduce musica', 'reproduce la musica',
                'reproduce mi musica', 'reproduce una cancion', 'reproduce algo',
                'reproduce una cancion cualquiera')):
        return ('No dispongo de ese contexto musical. Indica «la canción» y su título, '
                'o pide continuar la reproducción. Puedes cancelar.')
    return None


class SeguimientoAclaraciones:
    """Consume la respuesta una vez; un comando nuevo invalida lo pendiente.

    Un número de turno evita que un análisis antiguo registre una pregunta
    después de que otro hilo ya haya recibido una nueva instrucción.
    Los bloqueos nunca abarcan voz, almacenamiento, Spotify ni llamadas Tk.
    """
    def __init__(self, *, caducidad=120, reloj=time.monotonic):
        self._reloj = reloj
        self._caducidad = caducidad
        self._bloqueo = threading.Lock()
        self._turno = 0
        self._pendiente = None

    def guardar(self, datos, turno, *, vence=None):
        with self._bloqueo:
            if turno != self._turno:
                return False
            limite = self._reloj() + self._caducidad
            self._pendiente = (deepcopy(datos), min(limite, vence) if vence is not None else limite)
            return True

    def descartar(self, turno):
        with self._bloqueo:
            if turno == self._turno:
                self._pendiente = None

    def recibir(self, texto, ahora):
        t = normalizar_intencion(texto)
        with self._bloqueo:
            self._turno += 1
            turno = self._turno
            pendiente, self._pendiente = self._pendiente, None
        cancelacion = t in ('cancelar', 'cancela', 'cancelar aclaracion', 'cancela la aclaracion', 'olvida eso', 'no')
        periodos = {'de la manana': 'am', 'por la manana': 'am', 'am': 'am',
                    'de la tarde': 'pm', 'por la tarde': 'pm', 'de la noche': 'pm', 'pm': 'pm'}
        original = preparar_comando(texto)
        hora_completa = re.fullmatch(r'(?:a las? )?(\d{1,2}):(\d{2})', original)
        titulo = re.fullmatch(r'(?:la )?canci[oó]n\s+(.+)', original)
        es_respuesta = (re.match(r'^(?:(?:de la|por la) (?:manana|tarde|noche)|am|pm|si)\b', t)
                        or re.match(r'^(?:a las? )?\d{1,2}:', original)
                        or (titulo is not None and (pendiente is not None or t != 'cancion anterior'))
                        or (pendiente and t.startswith('no ')))
        mensaje = lambda contenido: (turno, {'tipo': 'mensaje', 'mensaje': contenido})
        inteligente = pendiente and pendiente[0]['tipo'] == 'recordatorio_inteligente'
        if inteligente:
            # La propuesta se consumió bajo el mismo bloqueo que las aclaraciones
            # tradicionales: dos «sí» no pueden obtener los mismos parámetros.
            from eva_inteligencia.propuestas_recordatorios import responder_propuesta
            respuesta = None if cancelacion else responder_propuesta(pendiente[0], texto, ahora)
            if (respuesta is not None or cancelacion) and self._reloj() >= pendiente[1]:
                return turno, dict(tipo='mensaje', estado='caducado',
                    mensaje='La propuesta caducó. No se guardó nada. Repite la solicitud completa.')
            if cancelacion:
                return turno, dict(tipo='mensaje', estado='cancelado',
                    mensaje='Propuesta cancelada. No se guardó ningún recordatorio.')
            if respuesta is not None:
                siguiente = respuesta.pop('pendiente', None)
                if siguiente is not None and not self.guardar(siguiente, turno, vence=pendiente[1]):
                    return mensaje('Llegó otra instrucción. Repite el recordatorio completo para revisarlo.')
                return turno, respuesta
        if cancelacion:
            return mensaje('Aclaración cancelada. No se realizó ninguna acción pendiente.' if pendiente
                           else 'No hay una aclaración pendiente que cancelar.')
        if not es_respuesta:
            return turno, None  # Comando independiente; no concatenar texto libre.
        if pendiente is None or self._reloj() >= pendiente[1]:
            return mensaje('No hay una aclaración vigente. Repite la instrucción completa.')
        datos = pendiente[0]
        if datos['tipo'] == 'periodo' and (t in periodos or hora_completa):
            parametros = datos['alternativas'].get(periodos.get(t))
            if hora_completa:
                # Sólo seleccionar una alternativa ya validada; no inventar otra hora.
                parametros = next((p for p in datos['alternativas'].values()
                    if (p['hora'], p['minuto']) == (int(hora_completa[1]), int(hora_completa[2]))), None)
            if parametros is not None:
                parametros = validar_accion('crear_recordatorio', parametros)
                momento = datetime.strptime(parametros['fecha'], '%Y-%m-%d').replace(
                    hour=parametros['hora'], minute=parametros['minuto'])
                if momento > ahora:
                    return turno, {'tipo': 'recordatorio', 'parametros': parametros}
            return mensaje('Esa fecha y hora no son válidas o ya pasaron. Repite el recordatorio completo.')
        if datos['tipo'] == 'musica' and titulo:
            consulta = titulo[1].strip()
            if detectar_compuesta('reproduce la canción ' + consulta):
                return mensaje('Indica una sola canción, sin añadir otras instrucciones.')
            consulta = titulo_literal('la canción ' + consulta) or consulta
            try:
                validar_accion('spotify_reproducir', {'accion': 'reproducir_cancion', 'consulta': consulta})
            except ValueError:
                return mensaje('Indica un título válido en una instrucción completa.')
            return turno, {'tipo': 'musica', 'consulta': consulta}
        return mensaje('La respuesta no completa los datos solicitados. Repite la instrucción completa.')
