"""Adaptador de sólo diagnóstico. No importa main, Tkinter, voz ni ejecutores."""
from pathlib import Path
import joblib
import sklearn

from persistencia import ErrorPersistencia
from .entrenamiento import puntuar, decidir, DESCONOCIDO
from .parametros import extraer_parametros
from .seguridad import revisar_seguridad
from .texto import normalizar
from .contexto import analizar_contexto, validar_contexto
from .modelo_oficial import RUTA_MODELO


class InterpreteLocal:
    def __init__(self, ruta_modelo=RUTA_MODELO, personales=None):
        # Sólo artefactos generados aquí y de confianza: joblib NO es un formato seguro
        # para archivos descargados ni proporcionados por comandos del usuario.
        self.paquete = joblib.load(Path(ruta_modelo))
        if self.paquete.get('version_sklearn') != sklearn.__version__ or self.paquete.get('formato') != 1:
            raise ValueError('Modelo incompatible. Repite el entrenamiento con este entorno.')
        self.personales = personales

    def proponer(self, texto, *, comando_local_atendido, ahora=None):
        # El llamador debe declarar explícitamente el resultado del enrutador local.
        if comando_local_atendido is not False:
            return {'estado': 'prioridad_local', 'ejecutable': False}
        contexto = analizar_contexto(texto, ahora)
        if contexto is not None:
            return contexto
        problema = revisar_seguridad(texto)
        if problema:
            return {'estado': 'aclaracion', 'pregunta': problema, 'ejecutable': False}
        if self.personales is not None:
            try:
                personal = self.personales.interpretar(texto, ahora)
            except ErrorPersistencia as error:
                return {'estado': 'error', 'mensaje': str(error), 'ejecutable': False}
            if personal is not None:
                return personal
        paquete = self.paquete
        scores = puntuar(paquete['modelo'], [normalizar(texto)], paquete['referencias'])
        intencion = str(decidir(scores, paquete['umbrales'])[0])
        if intencion == DESCONOCIDO:
            return {'estado': 'desconocido', 'ejecutable': False,
                    'pregunta': 'No estoy segura de la instrucción. Reformúlala con una sola acción.'}
        contexto = validar_contexto(texto, intencion)
        if contexto is not None:
            contexto['intencion_candidata'] = intencion
            return contexto
        resultado = extraer_parametros(intencion, texto, ahora)
        resultado.update(origen='modelo_local', score=float(scores[1][0]), similitud=float(scores[3][0]))
        return resultado
