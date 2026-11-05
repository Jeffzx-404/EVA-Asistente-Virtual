"""Entrena y evalúa el clasificador de intenciones sin ejecutar comandos de EVA.

Uso: python -m eva_inteligencia.entrenar
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .texto import normalizar

BASE = Path(__file__).resolve().parent
DATOS = BASE / 'datos' / 'ejemplos.csv'
MODELO = BASE / 'modelo_intenciones.joblib'
METADATOS = BASE / 'modelo_info.json'


def leer_ejemplos(ruta: Path = DATOS):
    with ruta.open(encoding='utf-8-sig', newline='') as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        raise ValueError('No existen ejemplos')
    frases, intenciones = [], []
    vistos = {}
    for fila in filas:
        frase = normalizar(fila['frase'])
        intencion = fila['intencion'].strip()
        if not frase or not intencion:
            raise ValueError('Hay una frase o intención vacía')
        if frase in vistos:
            raise ValueError(f'Frase repetida: {frase!r} ({vistos[frase]}, {intencion})')
        vistos[frase] = intencion
        frases.append(frase)
        intenciones.append(intencion)
    cantidades = Counter(intenciones)
    if len(cantidades) < 2 or any(n < 4 for n in cantidades.values()):
        raise ValueError('Se requieren al menos 2 intenciones con 4 ejemplos cada una')
    return frases, intenciones


def construir_clasificador():
    return Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5), sublinear_tf=True)),
        ('modelo', LogisticRegression(max_iter=1500, class_weight='balanced', random_state=42, C=5.0)),
    ])


def entrenar():
    frases, clases = leer_ejemplos()
    x_train, x_test, y_train, y_test = train_test_split(
        frases, clases, test_size=0.25, stratify=clases, random_state=42
    )
    evaluacion = construir_clasificador()
    evaluacion.fit(x_train, y_train)
    predicciones = evaluacion.predict(x_test)
    exactitud = float(accuracy_score(y_test, predicciones))
    print('--- Evaluación de prueba (frases reservadas) ---')
    print(classification_report(y_test, predicciones, zero_division=0))
    print(f'Exactitud del conjunto de prueba: {exactitud:.1%} ({len(x_test)} frases)')
    print('ATENCIÓN: es un conjunto pequeño y sintético; no es una garantía de precisión real.')

    # Modelo final: utiliza todos los ejemplos después de medir con conjunto separado.
    modelo = construir_clasificador()
    modelo.fit(frases, clases)
    # Este archivo solo debe cargarse si fue creado por el propietario a partir de código confiable.
    joblib.dump({'modelo': modelo, 'frases_entrenamiento': frases}, MODELO)
    info = {
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'version_python': platform.python_version(),
        'version_sklearn': sklearn.__version__,
        'ejemplos': len(frases),
        'clases': dict(Counter(clases)),
        'exactitud_reserva': exactitud,
        'sha256_datos': hashlib.sha256(DATOS.read_bytes()).hexdigest(),
    }
    METADATOS.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Modelo creado: {MODELO}')
    print('Puedes probarlo con: python -m eva_inteligencia.probar')
    return exactitud


if __name__ == '__main__':
    entrenar()
