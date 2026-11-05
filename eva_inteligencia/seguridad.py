"""Validaciones locales previas; no ejecuta ni autoriza operaciones."""
import re
from .texto import normalizar

INTENCIONES = frozenset({
    'consultar_hora', 'consultar_fecha', 'crear_recordatorio', 'consultar_recordatorios',
    'crear_alarma', 'detener_alarma', 'abrir_aplicacion', 'cerrar_aplicacion',
    'spotify_reproducir', 'spotify_pausar', 'ayuda',
})
APLICACIONES = {
    'calculadora': ('calculadora',), 'bloc de notas': ('bloc de notas', 'notepad'),
    'paint': ('paint',), 'explorador': ('explorador de archivos', 'explorador'),
    'chrome': ('google chrome', 'chrome'), 'spotify': ('spotify',),
}


def revisar_seguridad(texto):
    if not isinstance(texto, str) or not texto.strip() or len(texto) > 1000:
        return 'Texto vacío o demasiado largo.'
    t = normalizar(texto)
    if re.search(r'\b(?:borra\w*|elimin\w*|formate\w*|desinstal\w*|reinici\w*|'
                 r'suprim\w*|modific\w*|edita\w*|cancela\w*|antivirus|registro|'
                 r'power(?:shell)?|cmd|regedit|terminal|sudo|shutdown|exec|eval)\b', t):
        return 'Acción no autorizada por la inteligencia local.'
    if re.search(r'[a-z]:[\\/]|\\\\|[;&|`]|\$\(|__', texto, re.I):
        return 'No se admiten rutas, código ni cadenas de órdenes.'
    if re.search(r'\b(?:no|nunca|jamas)\b', t):
        return 'La instrucción contiene una negación; aclara qué deseas hacer.'
    if re.search(r'\b(?:y|luego|despues) (?:abre|cierra|pon|pausa|borra|ejecuta|inicia)\b', t):
        return 'Indica una sola acción por solicitud.'
    if re.search(r'\b(?:si|cuando)\b', t):
        return 'No se admiten condiciones o eventos; indica una fecha y hora.'
    return None
