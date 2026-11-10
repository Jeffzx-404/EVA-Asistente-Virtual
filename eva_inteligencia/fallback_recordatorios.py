"""Interpretación experimental de recordatorios. Nunca guarda ni confirma por voz."""
from datetime import datetime
import os

from .fallback_lectura import FallbackLectura
from .propuestas_recordatorios import preparar_solicitud


def _cargar_analizador():
    from .integracion import InterpreteLocal
    from .entrenamiento import puntuar, decidir
    from .texto import normalizar
    motor = InterpreteLocal()  # Artefacto oficial, sin datos personales ni entrenamiento.

    def analizar(texto):
        paquete = motor.paquete
        scores = puntuar(paquete['modelo'], [normalizar(texto)], paquete['referencias'])
        return str(decidir(scores, paquete['umbrales'])[0])
    return analizar


class FallbackRecordatorios(FallbackLectura):
    """Misma cola acotada y plazos; contrato distinto: propuesta de un recordatorio."""
    def __init__(self, activado=False, *, ahora=datetime.now, **opciones):
        super().__init__(activado, **opciones)
        self._ahora = ahora

    def _respuesta_directa(self, texto):
        return None  # No heredar permisos ni regla determinista de ayuda.

    @property
    def acepta_confirmaciones(self):
        return self.activado and not self._cerrado.is_set()

    def _cargar(self):
        return _cargar_analizador()

    def _interpretar(self, texto, analizar):
        if analizar(texto) != 'crear_recordatorio':
            return None
        return preparar_solicitud(texto, self._ahora())


def crear_fallback_recordatorios():
    return FallbackRecordatorios(os.environ.get('EVA_INTELIGENCIA_RECORDATORIOS') == '1')
