"""Etapa 2 offline: ampliación sintética, reservas inmutables y calibración segura."""
import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

import joblib
import numpy as np
import sklearn
from sklearn.model_selection import StratifiedGroupKFold
from . import entrenamiento as e

ANTERIOR = e.BASE / 'experimentos/v03_01'


def huella(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def guardar(ruta, objeto):
    with Path(ruta).open('x', encoding='utf-8') as archivo:
        json.dump(objeto, archivo, ensure_ascii=False, indent=2, allow_nan=False)


def preparar():
    original = json.loads((ANTERIOR / 'particiones.json').read_text(encoding='utf-8'))
    reserva = [f for f in original if f['conjunto'] == 'prueba']
    desarrollo = [dict(texto=f['texto'], intencion=f['intencion'], origen='v03')
                  for f in original if f['conjunto'] != 'prueba']
    desarrollo += [dict(**f, origen='ampliacion_sintetica')
                   for f in e.leer_corpus(e.BASE / 'datos/ampliacion_v04.csv')]
    # Las reservas sólo se consultan aquí como texto para excluir familias parecidas.
    protegidos = reserva + e.leer_corpus(e.BASE / 'datos/desafio_independiente.csv') + e.leer_corpus(e.BASE / 'datos/desafio_v04.csv')
    grupos = e.agrupar(desarrollo + protegidos)
    bloqueados = set(grupos[len(desarrollo):])
    vistos, admitidos, excluidos = set(), [], []
    for i, fila in enumerate(desarrollo):
        clave = e.normalizar(fila['texto'])
        motivo = 'familia_similar_a_reserva' if grupos[i] in bloqueados else 'duplicado' if clave in vistos else None
        registro = dict(**fila, grupo=int(grupos[i]))
        if motivo:
            excluidos.append(dict(**registro, motivo=motivo))
        else:
            admitidos.append(registro)
            vistos.add(clave)
    y = np.array([f['intencion'] for f in admitidos])
    g = np.array([f['grupo'] for f in admitidos])
    train, val = next(StratifiedGroupKFold(4, shuffle=True, random_state=104).split(y, y, g))
    if set(y[train]) != set(y) or set(y[val]) != set(y):
        raise ValueError('Faltan clases en desarrollo; se requieren más familias.')
    for nombre, ids in (('entrenamiento', train), ('validacion', val)):
        for i in ids:
            admitidos[i]['conjunto'] = nombre
    return admitidos, excluidos, reserva


def grilla(es_svm):
    for score in ((-.5, 0., .25, .5, .75, 1., 1.5) if es_svm else (.15, .2, .3, .4, .5, .6, .75, .9)):
        for margen in (0., .1, .2, .4):
            for similitud in (0., .2, .35, .5):
                yield dict(score=score, margen=margen, similitud=similitud)
    yield dict(score=1e9, margen=0., similitud=0.)  # Alternativa explícita: rechazar todo.


def calibrar_seguro(etiquetas, scores, es_svm=False, por_intencion=False):
    """Maximizar aciertos aceptados sujeto a cero errores OBSERVADOS en validación.

    No equivale a garantizar seguridad futura. Umbral por clase sólo con >= 5
    ejemplos reales y >= 3 propuestas correctas observadas; si no, hereda global.
    """
    y = np.asarray(etiquetas)
    opciones = list(grilla(es_svm))
    mejor, cuenta = opciones[-1], -1
    for u in opciones:
        pred = e.decidir(scores, u)
        aceptado = pred != e.DESCONOCIDO
        if np.any(aceptado & (pred != y)):
            continue
        n = int(aceptado.sum())
        if n > cuenta:
            mejor, cuenta = u, n
    resultado = deepcopy(mejor)
    if por_intencion:
        resultado['por_intencion'] = {}
        for clase in sorted(set(scores[0]) - {e.DESCONOCIDO}):
            if np.sum(y == clase) < 5:
                continue
            mascara = scores[0] == clase
            parcial = tuple(v[mascara] for v in scores)
            ganador, maximo = mejor, int(np.sum(e.decidir(parcial, mejor) != e.DESCONOCIDO))
            for u in opciones:
                pred = e.decidir(parcial, u)
                aceptado = pred != e.DESCONOCIDO
                n = int(aceptado.sum())
                if not np.any(aceptado & (pred != y[mascara])) and n >= 3 and n > maximo:
                    ganador, maximo = u, n
            resultado['por_intencion'][str(clase)] = deepcopy(ganador)
    return resultado


def evaluar_paquete(paquete, filas):
    scores = e.puntuar(paquete['modelo'], [e.normalizar(f['texto']) for f in filas], paquete['referencias'])
    resultado = e.evaluar(filas, e.decidir(scores, paquete['umbrales']))
    conocidos = [f for f in filas if f['intencion'] != e.DESCONOCIDO]
    resultado['cobertura_correcta_conocidas'] = (sum(f['intencion'] == p for f, p in zip(filas, e.decidir(scores, paquete['umbrales']))
                                                   if f['intencion'] != e.DESCONOCIDO) / len(conocidos))
    return resultado


def evaluar_adaptador(ruta, filas):
    from .integracion import InterpreteLocal
    motor = InterpreteLocal(ruta)
    detalles, principales, pred = [], [], []
    for fila in filas:
        r = motor.proponer(fila['texto'], comando_local_atendido=False, ahora=datetime(2026, 11, 4, 10))
        detalles.append(dict(**fila, resultado=r))
        if fila['esperado'] != 'aclaracion':
            principales.append(fila)
            pred.append(r.get('intencion') if r['estado'] == 'propuesta' else e.DESCONOCIDO)
    return dict(metricas=e.evaluar(principales, pred), detalles=detalles,
                incompletas_ambiguas_propuestas=sum(f['esperado'] == 'aclaracion' and f['resultado']['estado'] == 'propuesta' for f in detalles),
                categorias={cat: dict(total=sum(f['categoria'] == cat for f in detalles),
                                     propuestas=sum(f['categoria'] == cat and f['resultado']['estado'] == 'propuesta' for f in detalles))
                            for cat in sorted({f['categoria'] for f in filas})})


def ejecutar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=False)
    inicio = time.perf_counter()
    rutas = [ANTERIOR / 'particiones.json', e.BASE / 'datos/ejemplos.csv',
             e.BASE / 'datos/desafio_independiente.csv', e.BASE / 'datos/desafio_v04.csv',
             e.BASE / 'datos/ampliacion_v04.csv', *sorted(ANTERIOR.glob('*.joblib'))]
    hashes = {str(p.relative_to(e.BASE)): huella(p) for p in rutas}
    datos, excluidos, prueba = preparar()
    guardar(salida / 'particiones.json', datos)
    guardar(salida / 'excluidos.json', excluidos)
    train = [f for f in datos if f['conjunto'] == 'entrenamiento']
    val = [f for f in datos if f['conjunto'] == 'validacion']
    textos = [e.normalizar(f['texto']) for f in train]
    y_val = [f['intencion'] for f in val]
    informe = dict(hashes=hashes, sklearn=sklearn.__version__, activado=False,
                   criterio='Cero propuestas erróneas en validación; maximizar cobertura correcta. Empate: global primero.',
                   distribucion={c: dict(Counter(f['intencion'] for f in datos if f['conjunto'] == c))
                                 for c in ('entrenamiento', 'validacion')}, excluidos=len(excluidos), modelos={})
    paquetes = {}
    for nombre, modelo in e.candidatos().items():
        if nombre == 'naive_bayes':
            continue
        modelo.fit(textos, [f['intencion'] for f in train])
        refs = modelo.named_steps['tfidf'].transform(textos)
        scores = e.puntuar(modelo, [e.normalizar(f['texto']) for f in val], refs)
        for individual in (False, True):
            clave = nombre + ('_por_intencion' if individual else '_global')
            umbrales = calibrar_seguro(y_val, scores, nombre == 'svm_lineal', individual)
            paquete = dict(modelo=modelo, referencias=refs, umbrales=umbrales, formato=1, version_sklearn=sklearn.__version__)
            paquetes[clave] = paquete
            informe['modelos'][clave] = dict(umbrales=umbrales, validacion=evaluar_paquete(paquete, val))
    seleccionado = max(paquetes, key=lambda n: informe['modelos'][n]['validacion']['cobertura_correcta_conocidas'])
    informe['seleccion_validacion'] = seleccionado
    guardar(salida / 'seleccion_antes_de_prueba.json', informe)
    # Se ha cerrado selección y calibración: sólo ahora se evalúan los modelos.
    for nombre, paquete in paquetes.items():
        joblib.dump(paquete, salida / (nombre + '.joblib'), compress=3)
    for nombre in ('lr_caracteres_original', 'svm_lineal'):
        clave = 'anterior_' + nombre
        paquetes[clave] = joblib.load(ANTERIOR / (nombre + '.joblib'))
        informe['modelos'][clave] = {}
    with (e.BASE / 'datos/desafio_v04.csv').open(encoding='utf-8', newline='') as archivo:
        desafio = list(csv.DictReader(archivo))
    for nombre, paquete in paquetes.items():
        for conjunto, filas in (('prueba_conservada', prueba), ('desafio_anterior', e.leer_corpus(e.BASE / 'datos/desafio_independiente.csv')),
                               ('desafio_nuevo', desafio)):
            informe['modelos'][nombre][conjunto] = evaluar_paquete(paquete, filas)
    informe['adaptador'] = {
        'anterior': evaluar_adaptador(ANTERIOR / 'lr_caracteres_original.joblib', desafio),
        'seleccionado': evaluar_adaptador(salida / (seleccionado + '.joblib'), desafio)}
    # Gate conservador predefinido: mejora de cobertura en ambas reservas y ningún
    # aumento de errores/reducción de rechazo. Sólo recomendación, nunca activación.
    anterior = informe['modelos']['anterior_lr_caracteres_original']
    nuevo = informe['modelos'][seleccionado]
    mejora = all(nuevo[c]['cobertura_correcta_conocidas'] > anterior[c]['cobertura_correcta_conocidas']
                 and nuevo[c]['aceptaciones_erroneas_total'] <= anterior[c]['aceptaciones_erroneas_total']
                 and nuevo[c]['rechazo_desconocidas'] >= anterior[c]['rechazo_desconocidas']
                 for c in ('prueba_conservada', 'desafio_nuevo'))
    seguro = (informe['adaptador']['seleccionado']['metricas']['aceptaciones_erroneas_total'] == 0
              and informe['adaptador']['seleccionado']['incompletas_ambiguas_propuestas'] == 0)
    informe['recomendacion'] = seleccionado if mejora and seguro else 'conservar_anterior'
    informe['segundos_totales'] = time.perf_counter() - inicio
    if hashes != {str(p.relative_to(e.BASE)): huella(p) for p in rutas}:
        raise RuntimeError('Se modificaron entradas o modelos anteriores durante el experimento.')
    guardar(salida / 'informe.json', informe)
    print(json.dumps(dict(seleccion=seleccionado, recomendacion=informe['recomendacion'],
                         entrenamiento=len(train), validacion=len(val), excluidos=len(excluidos)), ensure_ascii=False))
    return informe


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    ejecutar(parser.parse_args().salida)
