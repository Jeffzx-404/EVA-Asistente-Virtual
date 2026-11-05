"""Ruta única del modelo distribuido. Importar aquí no carga sklearn ni modelos."""
from pathlib import Path


RUTA_MODELO = Path(__file__).resolve().parent / 'modelos' / 'intenciones_lr_v03.joblib'
