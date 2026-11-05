"""Normalización conservadora para comandos de voz en español."""
import re
import unicodedata


def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        raise TypeError('El comando debe ser texto')
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto.casefold())
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r'^\s*(?:oye\s+)?eva\b[\s,.:;!¡¿?\-]*', '', texto)
    texto = re.sub(r'[^\w\s]', ' ', texto)
    return ' '.join(texto.split())
