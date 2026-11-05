"""Experimento reproducible offline. No publica ni activa modelos en EVA."""
from __future__ import annotations

import argparse
import csv
from difflib import SequenceMatcher
import hashlib
import json
import platform
from pathlib import Path
import re
import time

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from .texto import normalizar

BASE = Path(__file__).resolve().parent
DESCONOCIDO = 'fuera_de_alcance'
SEMILLA = 42


def leer_corpus(ruta):
    with Path(ruta).open(encoding='utf-8-sig', newline='') as archivo:
        filas = list(csv.DictReader(archivo))
    filas = [{'texto': f.get('texto', f.get('frase', '')), 'intencion': f.get('intencion')} for f in filas]
    from .seguridad import INTENCIONES
    if not filas or any(not f.get('texto', '').strip() or f.get('intencion') not in
                        INTENCIONES | {DESCONOCIDO} for f in filas):
        raise ValueError('Corpus vacío o con texto/intención incorrectos.')
    return filas


def plantilla(texto):
    texto = normalizar(texto)
    texto = re.sub(r'\b(?:por favor|podrias|puedes|porfa|quisiera|quiero que)\b', '', texto)
    texto = re.sub(r'\b(?:\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\b', 'NUM', texto)
    return ' '.join(texto.split())


def agrupar(filas):
    """Componentes conexas: igualdad normalizada/plantilla o similitud >= .80.

    Es una heurística léxica, no garantiza reconocer todas las paráfrasis.
    Nunca se usan etiquetas para decidir si dos frases pertenecen a una familia.
    """
    claves = [plantilla(f['texto']) for f in filas]
    padres = list(range(len(filas)))

    def raiz(i):
        while padres[i] != i:
            padres[i] = padres[padres[i]]
            i = padres[i]
        return i

    for i, a in enumerate(claves):
        for j in range(i):
            b = claves[j]
            if a == b or SequenceMatcher(None, a, b, autojunk=False).ratio() >= .80:
                padres[raiz(i)] = raiz(j)
    return np.array([raiz(i) for i in range(len(filas))])


def particionar(filas, grupos):
    etiquetas = np.array([f['intencion'] for f in filas])
    indices = np.arange(len(filas))
    desarrollo, prueba = next(StratifiedGroupKFold(5, shuffle=True, random_state=SEMILLA)
                             .split(indices, etiquetas, grupos))
    a, b = next(StratifiedGroupKFold(4, shuffle=True, random_state=SEMILLA + 1)
                .split(desarrollo, etiquetas[desarrollo], grupos[desarrollo]))
    particiones = {'entrenamiento': desarrollo[a], 'validacion': desarrollo[b], 'prueba': prueba}
    for nombre, ids in particiones.items():
        if set(etiquetas[ids]) != set(etiquetas):
            raise ValueError(f'{nombre} no contiene todas las clases; amplía familias del corpus.')
    return particiones


def candidatos():
    def caracteres():
        return TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5), sublinear_tf=True)
    return {
        'lr_caracteres_original': Pipeline([('tfidf', caracteres()), ('modelo',
            LogisticRegression(C=5, class_weight='balanced', max_iter=1500, random_state=SEMILLA))]),
        'lr_palabras_caracteres': Pipeline([('tfidf', FeatureUnion([
            ('caracteres', caracteres()), ('palabras', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True))])),
            ('modelo', LogisticRegression(C=5, class_weight='balanced', max_iter=1500, random_state=SEMILLA))]),
        'svm_lineal': Pipeline([('tfidf', caracteres()), ('modelo',
            LinearSVC(C=1, class_weight='balanced', random_state=SEMILLA))]),
        'naive_bayes': Pipeline([('tfidf', caracteres()), ('modelo', ComplementNB(alpha=.5))]),
    }


def puntuar(modelo, textos, referencias):
    matriz = modelo.named_steps['tfidf'].transform(textos)
    clasificador = modelo.named_steps['modelo']
    scores = (clasificador.predict_proba(matriz) if hasattr(clasificador, 'predict_proba')
              else clasificador.decision_function(matriz))
    orden = np.sort(scores, axis=1)
    return (clasificador.classes_[scores.argmax(axis=1)], scores.max(axis=1),
            orden[:, -1] - orden[:, -2], cosine_similarity(matriz, referencias).max(axis=1))


def decidir(puntuaciones, umbrales):
    clases, scores, margenes, similitudes = puntuaciones
    por_clase = umbrales.get('por_intencion', {})
    limites = [por_clase.get(str(c), umbrales) for c in clases]
    aceptar = ((scores >= np.array([u['score'] for u in limites])) &
               (margenes >= np.array([u['margen'] for u in limites])) &
               (similitudes >= np.array([u['similitud'] for u in limites])) & (clases != DESCONOCIDO))
    return np.where(aceptar, clases, DESCONOCIDO)


def objetivo(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    desconocidos = y == DESCONOCIDO
    far = float(np.mean(pred[desconocidos] != DESCONOCIDO)) if desconocidos.any() else 0.
    erroneas = float(np.mean((pred != DESCONOCIDO) & (pred != y)))
    return float(f1_score(y, pred, average='macro', zero_division=0) - .5 * far - .5 * erroneas)


def calibrar(y_validacion, puntuaciones, es_svm=False):
    # Se invoca exclusivamente con validación. Grilla fijada antes de abrir prueba.
    mejor = None
    for score in ((-1., -.5, 0., .3, .6) if es_svm else (0., .2, .3, .4, .5, .6)):
        for similitud in (0., .2, .3, .4, .5, .6):
            for margen in (0., .05, .1, .2):
                umbrales = dict(score=score, similitud=similitud, margen=margen)
                valor = objetivo(y_validacion, decidir(puntuaciones, umbrales))
                if mejor is None or valor > mejor[0]:
                    mejor = valor, umbrales
    return mejor[1]


def evaluar(filas, pred):
    y = np.array([f['intencion'] for f in filas])
    pred = np.asarray(pred)
    etiquetas = sorted(set(y) | set(pred))
    desconocidos = y == DESCONOCIDO
    conocidos = ~desconocidos
    aceptados = pred != DESCONOCIDO
    return {
        'n': len(y), 'exactitud': float(np.mean(y == pred)),
        'f1_macro': float(f1_score(y, pred, average='macro', zero_division=0)),
        'precision_aceptadas': float(np.mean(y[aceptados] == pred[aceptados])) if aceptados.any() else None,
        'cobertura_conocidas': float(np.mean(aceptados[conocidos])) if conocidos.any() else None,
        'rechazo_desconocidas': float(np.mean(~aceptados[desconocidos])) if desconocidos.any() else None,
        'falsas_aceptaciones_desconocidas': int(np.sum(aceptados & desconocidos)),
        'aceptaciones_erroneas_total': int(np.sum(aceptados & (pred != y))),
        'por_intencion': classification_report(y, pred, output_dict=True, zero_division=0),
        'etiquetas_matriz': etiquetas,
        'matriz_confusion': confusion_matrix(y, pred, labels=etiquetas).tolist(),
        'errores': [{'texto': f['texto'], 'real': f['intencion'], 'prediccion': str(p)}
                    for f, p in zip(filas, pred) if f['intencion'] != p],
    }


def ejecutar(corpus, desafio, salida):
    filas = leer_corpus(corpus)
    grupos = agrupar(filas)
    particiones = particionar(filas, grupos)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=False)  # Nunca reemplazar un experimento anterior.
    json_guardar = lambda nombre, datos: (salida / nombre).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    manifiesto = [{'indice': int(i), 'grupo': int(grupos[i]), 'conjunto': conjunto, **filas[i]}
                  for conjunto, ids in particiones.items() for i in ids]
    json_guardar('particiones.json', manifiesto)
    informe = {'semilla': SEMILLA, 'python': platform.python_version(), 'sklearn': sklearn.__version__,
               'numpy': np.__version__, 'scipy': __import__('scipy').__version__,
               'sha256_corpus': hashlib.sha256(Path(corpus).read_bytes()).hexdigest(),
               'sha256_desafio': hashlib.sha256(Path(desafio).read_bytes()).hexdigest(),
               'familias': len(set(grupos)),
               'duplicados_normalizados': len(filas) - len({normalizar(f['texto']) for f in filas}),
               'familias_etiquetas_distintas': [int(g) for g in set(grupos) if len({
                   f['intencion'] for i, f in enumerate(filas) if grupos[i] == g}) > 1],
               'distribucion': {k: {c: sum(filas[i]['intencion'] == c for i in ids)
                                    for c in sorted({f['intencion'] for f in filas})}
                                for k, ids in particiones.items()}, 'candidatos': {}}
    obtener = lambda clave: [filas[i] for i in particiones[clave]]
    train, val, test = (obtener(k) for k in ('entrenamiento', 'validacion', 'prueba'))
    textos_train = [normalizar(f['texto']) for f in train]
    modelos = {}
    for nombre, modelo in candidatos().items():
        inicio = time.perf_counter()
        modelo.fit(textos_train, [f['intencion'] for f in train])
        referencias = modelo.named_steps['tfidf'].transform(textos_train)
        scores = puntuar(modelo, [normalizar(f['texto']) for f in val], referencias)
        umbrales = calibrar([f['intencion'] for f in val], scores, nombre == 'svm_lineal')
        pred = decidir(scores, umbrales)
        resultado = {'umbrales': umbrales, 'validacion': evaluar(val, pred),
                     'objetivo_validacion': objetivo([f['intencion'] for f in val], pred),
                     'segundos_entrenamiento_y_calibracion': time.perf_counter() - inicio}
        modelos[nombre] = {'modelo': modelo, 'referencias': referencias, 'umbrales': umbrales,
                           'version_sklearn': sklearn.__version__, 'formato': 1}
        informe['candidatos'][nombre] = resultado
    elegido = max(informe['candidatos'], key=lambda n: informe['candidatos'][n]['objetivo_validacion'])
    informe['seleccion_validacion'] = elegido
    # Hasta aquí ni las frases ni las etiquetas de prueba se han usado para ajustar.
    reto = leer_corpus(desafio)
    corpus_norm = {normalizar(f['texto']) for f in filas}
    if any(normalizar(f['texto']) in corpus_norm for f in reto):
        raise ValueError('El desafío contiene frases ya presentes en el corpus.')
    for nombre, paquete in modelos.items():
        for clave, conjunto in (('prueba', test), ('desafio', reto)):
            scores = puntuar(paquete['modelo'], [normalizar(f['texto']) for f in conjunto], paquete['referencias'])
            informe['candidatos'][nombre][clave] = evaluar(conjunto, decidir(scores, paquete['umbrales']))
        joblib.dump(paquete, salida / f'{nombre}.joblib', compress=3)
    from .motor import MotorIntenciones
    original = MotorIntenciones(usar_alias=False)
    informe['original_distribuido_desafio'] = evaluar(reto, [
        original.clasificar(f['texto'])['intencion'] or DESCONOCIDO for f in reto])
    # Comparación limpia del algoritmo original con umbrales antiguos y sólo train.
    base = modelos['lr_caracteres_original']
    informe['base_umbrales_v02_prueba'] = evaluar(test, decidir(puntuar(
        base['modelo'], [normalizar(f['texto']) for f in test], base['referencias']),
        {'score': .25, 'similitud': .34, 'margen': 0.}))
    informe['activado'] = False
    json_guardar('informe.json', informe)
    lineas = ['# Evaluación local (sin activación)', '',
              f'Selección por validación: **{elegido}**. Prueba no interviene en selección.', '',
              '| Modelo | F1 validación | F1 prueba | Precisión aceptadas | Rechazo desconocidas | F1 desafío |',
              '|---|---:|---:|---:|---:|---:|']
    for nombre, r in informe['candidatos'].items():
        p = r['prueba']
        lineas.append(f"| {nombre} | {r['validacion']['f1_macro']:.3f} | {p['f1_macro']:.3f} | "
                      f"{p['precision_aceptadas']} | {p['rechazo_desconocidas']} | {r['desafio']['f1_macro']:.3f} |")
    lineas += ['', 'La matriz, métricas por intención y todos los errores están en informe.json.',
               'Desafío sintético separado: no representa habla real ni prueba independencia semántica.',
               'No se reentrena con prueba ni se reemplaza el modelo original.']
    (salida / 'INFORME.md').write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=BASE / 'datos' / 'ejemplos.csv')
    parser.add_argument('--desafio', type=Path, default=BASE / 'datos' / 'desafio_independiente.csv')
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    informe = ejecutar(args.corpus, args.desafio, args.salida)
    print('Experimento guardado. Selección por validación:', informe['seleccion_validacion'])


if __name__ == '__main__':
    main()
