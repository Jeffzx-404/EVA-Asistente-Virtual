"""Protección léxica previa, sin clasificador, persistencia ni ejecutores."""
import re
from comandos_voz import preparar_comando, normalizar_intencion
from eva_inteligencia.contexto import INICIO_ORDEN, analizar_contexto

COMILLAS = r'"[^"\n]+"|«[^»\n]+»|“[^”\n]+”|\x27[^\x27\n]+\x27'


def titulo_literal(texto, *, exigir_peticion=False):
    """Un título delimitado completo, nunca una orden añadida fuera de comillas."""
    t = preparar_comando(texto)
    m = re.fullmatch(r'(?P<peticion>(?:reproduce|reproducir|pon|ponme|quiero escuchar|quiero o[ií]r|escuchar)\s+)?'
                     r'(?:la )?canci[oó]n\s+(?P<titulo>' + COMILLAS + r')', t)
    return m['titulo'][1:-1] if m and (not exigir_peticion or m['peticion']) else None


def detectar_compuesta(texto):
    # Enmascarar los literales impide interpretar «Dime y abre» como dos órdenes
    # dentro de un título. Las órdenes fuera de las comillas siguen visibles.
    t = preparar_comando(texto)
    # Sólo los títulos explícitos son literales; citar una segunda orden fuera
    # de una petición musical no debe ocultarla a la protección.
    protegido = re.sub(r'(\bcanci[oó]n\s+)(' + COMILLAS + r')',
                       r'\1titulo literal', t)
    protegido = re.sub(r'["«»“”\x27]', '', protegido)
    protegido = re.sub(r'\b(y|e|luego|después|además)\s+por favor\s+', r'\1 ', protegido)
    # Sólo para detectar la composición: conservar la negación y reconocer
    # estas formas de subjuntivo que el segmentador anterior no separaba.
    protegido = re.sub(r'\b(no|nunca)\s+(abras|cierres)\b',
                       lambda m: m[1] + ' ' + {'abras': 'abre', 'cierres': 'cierra'}[m[2]], protegido)
    contexto = analizar_contexto(protegido)
    if not contexto or contexto['tipo'] not in ('multiple_o_alternativa', 'multiples_objetos'):
        return None
    solicitudes = contexto['solicitudes']
    if contexto['tipo'] != 'multiples_objetos':
        # El analizador de diagnóstico también separa puntuación en nombres.
        # Exigir una segunda petición evita rechazar «Juan Luis Guerra 4.40».
        segunda_orden = any(re.match(r'^(?:(?:y|e|luego|ademas) )?(?:no |nunca )?' + INICIO_ORDEN + r'\b',
                                    normalizar_intencion(s['fragmento']))
                            for s in solicitudes[1:])
        if not segunda_orden:
            return None
    return {'motivo': 'La instrucción contiene varias solicitudes. Envía una sola; no ejecuté ninguna parte.',
            'intenciones': sorted({i for s in solicitudes for i in s['intenciones_posibles']})}
