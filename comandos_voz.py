"""Preparación del texto y reglas acotadas para los comandos de voz."""

import os
import re
import unicodedata


def preparar_comando(texto):
    """Quitar el vocativo EVA sin dañar palabras como 'llevar' o 'evaluar'.

    Conservar tildes, ñ y puntuación interior: pueden pertenecer al texto de un
    recordatorio, a una búsqueda o a una hora como 05:30.
    """
    texto = unicodedata.normalize("NFC", texto).lower().strip()
    bordes = " \t\r\n¿?¡!.,;:"
    texto = texto.strip(bordes)
    texto = re.sub(r"^eva\b[\s¿?¡!.,;:]*", "", texto)
    texto = re.sub(r"[\s¿?¡!.,;:]+eva$", "", texto)
    return texto.strip(bordes)


def normalizar_intencion(texto):
    """Vista solo para comparar intenciones; no se usa como texto del usuario."""
    texto = unicodedata.normalize("NFD", preparar_comando(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", texto).split())


def es_consulta_hora(texto):
    # Coincidencia de la frase completa: 'hora' en una alarma, un recordatorio
    # o una consulta sobre otro país no debe activar la hora local.
    texto = normalizar_intencion(texto)
    texto = re.sub(r"^por favor\s+|\s+por favor$", "", texto).strip()
    return bool(re.fullmatch(
        r"(?:que (?:hora|ahora) es(?: ahora)?|que h?oras(?: son)?|"
        r"(?:dime|dame) la hora(?: actual)?|hora actual|cual es la hora(?: actual)?)",
        texto,
    ))


def diagnosticar(evento, detalle):
    """Solo consola, activado temporalmente con EVA_DIAGNOSTICO_VOZ=1.

    No abre archivos ni registra audio, configuración o excepciones de servicios.
    Omite textos que podrían contener credenciales; repr evita controles de terminal.
    """
    if os.environ.get("EVA_DIAGNOSTICO_VOZ") != "1":
        return
    if evento == "whisper":
        privado = re.search(
            r"\b(?:clave|contrasena|password|token|secret|credencial|api|bearer)\w*\b",
            normalizar_intencion(detalle),
        ) or re.search(r"[\w-]{32,}", detalle)
        if privado:
            detalle = "[texto omitido: posible dato privado]"
    elif evento != "intencion":
        return
    try:
        print(f"[EVA diagnostico] {evento}: {detalle!r}")
    except (OSError, UnicodeError):
        # Una consola cerrada o con otra codificación no debe impedir un comando.
        pass
