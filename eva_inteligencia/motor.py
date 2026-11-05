"""Intérprete local: CLASIFICA, pero jamás ejecuta acciones."""
from __future__ import annotations

import json
import re
from pathlib import Path

import joblib
from sklearn.metrics.pairwise import cosine_similarity
import sklearn

from .alias_personales import cargar_alias
from .texto import normalizar

BASE = Path(__file__).resolve().parent
RUTA_MODELO = BASE / 'modelo_intenciones.joblib'
RUTA_INFO = BASE / 'modelo_info.json'

# Una petición de aviso sin asunto NO debe convertirse en una alarma o un
# recordatorio automático solo porque contenga una duración. La normalización
# ya eliminó tildes y signos de puntuación antes de aplicar esta expresión.
# Se admite un subconjunto explícito de frases completas, sin contenido extra.
_PETICION_AVISO_INCOMPLETO = re.compile(
    r'^(?:avisame|recuerdame|me\s+avisas|ponme\s+un\s+aviso'
    r'|(?:necesito|quiero|quisiera)\s+que\s+me\s+(?:avises|recuerdes)'
    r'|(?:puedes|podrias)\s+(?:avisarme|recordarme))'
    r'(?:\s+(?:en|dentro\s+de)\s+(?:\w+\s+){0,5}'
    r'(?:segundos?|minutos?|horas?|dias?)'
    r'|\s+(?:manana|pasado\s+manana)(?:\s+a\s+las\s+(?:\w+\s*){1,3})?'
    r'|\s+a\s+las\s+(?:\w+\s*){1,3})?$'
)


def _solicitud_aviso_incompleto(texto_normalizado: str) -> bool:
    """Detecta frases que piden un aviso pero omiten qué se debe recordar.

    Es una validación previa, no un extractor de fechas ni un ejecutor.
    Se usa coincidencia total para no bloquear frases como «avísame dentro
    de veinte minutos que estudie», que sí incluyen una descripción.
    """
    return _PETICION_AVISO_INCOMPLETO.fullmatch(texto_normalizado) is not None


class MotorIntenciones:
    def __init__(self, ruta_modelo: Path = RUTA_MODELO, ruta_info: Path = RUTA_INFO,
                 usar_alias: bool = True, ruta_alias: Path | None = None):
        ruta_modelo = Path(ruta_modelo)
        ruta_info = Path(ruta_info)
        if not ruta_modelo.is_file() or not ruta_info.is_file():
            raise FileNotFoundError('Falta el modelo. Ejecuta: python -m eva_inteligencia.entrenar')
        info = json.loads(ruta_info.read_text(encoding='utf-8'))
        if info['version_sklearn'] != sklearn.__version__:
            raise RuntimeError('La versión de scikit-learn cambió. Reentrena en este entorno.')
        # joblib puede ejecutar código al cargar: solamente abrir modelos locales de confianza.
        paquete = joblib.load(ruta_modelo)
        self.modelo = paquete['modelo']
        self.frases_entrenamiento = paquete['frases_entrenamiento']
        self.matriz_ejemplos = self.modelo.named_steps['tfidf'].transform(self.frases_entrenamiento)
        self.usar_alias = usar_alias
        self.ruta_alias = ruta_alias

    def clasificar(self, texto: str, umbral_prob: float = 0.25,
                  umbral_sim: float = 0.34) -> dict:
        texto_norm = normalizar(texto)
        if not texto_norm:
            return {'intencion': None, 'estado': 'desconocido', 'probabilidad': 0.0, 'similitud': 0.0, 'origen': 'vacio'}
        # Ninguna intención de esta versión permite borrar, editar ni cancelar datos.
        # Un clasificador de texto puede confundir 'elimina recordatorios' con 'consulta recordatorios'.
        if re.search(r'\b(?:elimina|eliminar|borra|borrar|suprime|suprimir|edita|editar|modifica|modificar|cancela|cancelar)\b', texto_norm):
            return {'intencion': None, 'estado': 'desconocido', 'probabilidad': 0.0, 'similitud': 0.0, 'origen': 'accion_no_admitida'}
        # Primero comprobar si falta el asunto del aviso, antes de consultar
        # alias o clasificador. No autorizar acciones con parámetros incompletos.
        if _solicitud_aviso_incompleto(texto_norm):
            return {
                'intencion': None,
                'estado': 'aclaracion',
                'probabilidad': None,
                'similitud': None,
                'origen': 'aviso_sin_descripcion',
                'pregunta': '¿Qué quieres que te recuerde? Si solo necesitas una alarma, indícalo.',
            }
        if self.usar_alias:
            alias = cargar_alias(self.ruta_alias)
            if texto_norm in alias:
                return {'intencion': alias[texto_norm], 'estado': 'propuesta',
                        'probabilidad': None, 'similitud': None, 'origen': 'alias_confirmado'}
        matriz = self.modelo.named_steps['tfidf'].transform([texto_norm])
        similitud = float(cosine_similarity(matriz, self.matriz_ejemplos).max())
        probabilidades = self.modelo.named_steps['modelo'].predict_proba(matriz)[0]
        indice = int(probabilidades.argmax())
        intencion = str(self.modelo.named_steps['modelo'].classes_[indice])
        confianza = float(probabilidades[indice])
        valida = (intencion != 'fuera_de_alcance' and confianza >= umbral_prob and similitud >= umbral_sim)
        return {
            'intencion': intencion if valida else None,
            'estado': 'propuesta' if valida else 'desconocido',
            'probabilidad': round(confianza, 3),
            'similitud': round(similitud, 3),
            'origen': 'modelo',
        }
