"""Comparación offline del adaptador anterior y contextual con el MISMO modelo.

Sólo corpus sintéticos fijos. No abre audio ni admite conversaciones como corpus.
La reserva de 58 ejemplos se verifica por hash, no se usa para ajustar ni evaluar reglas.
"""
import csv
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

from .entrenamiento import BASE, DESCONOCIDO, evaluar
from .integracion import InterpreteLocal
from .texto import normalizar

SALIDA = BASE / 'experimentos/contexto_v01'
MODELO = BASE / 'experimentos/v03_01/lr_caracteres_original.joblib'
AHORA = datetime(2026, 11, 4, 10)


def hash_archivo(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer(nombre):
    with (BASE / 'datos' / nombre).open(encoding='utf-8', newline='') as archivo:
        return list(csv.DictReader(archivo))


def medir(motor, filas):
    detalles, principales, predicciones = [], [], []
    for fila in filas:
        r = motor.proponer(fila['texto'], comando_local_atendido=False, ahora=AHORA)
        aceptada = r['estado'] == 'propuesta'
        detalles.append(dict(**fila, resultado=r))
        if fila['esperado'] != 'aclaracion':
            principales.append(fila)
            predicciones.append(r.get('intencion') if aceptada else DESCONOCIDO)
    metricas = evaluar(principales, predicciones)
    return dict(metricas=metricas, detalles=detalles,
                incompletas_total=sum(f['esperado'] == 'aclaracion' for f in filas),
                incompletas_propuestas=sum(f['esperado'] == 'aclaracion' and f['resultado']['estado'] == 'propuesta' for f in detalles),
                categorias={c: dict(total=sum(f['categoria'] == c for f in detalles),
                                    propuestas=sum(f['categoria'] == c and f['resultado']['estado'] == 'propuesta' for f in detalles))
                            for c in sorted({f['categoria'] for f in filas})})


def ejecutar():
    if (SALIDA / 'informe.json').exists() or (SALIDA / 'congelacion.json').exists():
        raise FileExistsError('La evaluación ya existe. No se sobrescribe ni se repite para ajustar reglas.')
    spec = importlib.util.spec_from_file_location('eva_inteligencia._baseline_contextual', SALIDA / 'integracion_anterior.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    anterior, nuevo = modulo.InterpreteLocal(MODELO), InterpreteLocal(MODELO)
    conjuntos = {'desarrollo_conocido_v04': leer('desafio_v04.csv'),
                'nuevo_natural': leer('contexto_natural.csv'),
                'nuevo_adversarial': leer('contexto_adversarial.csv')}
    nuevas = conjuntos['nuevo_natural'] + conjuntos['nuevo_adversarial']
    claves = [normalizar(f['texto']) for f in nuevas]
    if len(set(claves)) != len(claves):
        raise ValueError('Hay frases duplicadas en los desafíos nuevos.')
    # No reutilizar frases exactas del material ya empleado para desarrollo.
    previas = {normalizar(f['texto']) for f in conjuntos['desarrollo_conocido_v04']}
    if set(claves) & previas:
        raise ValueError('El desafío nuevo repite el desafío usado como desarrollo.')
    protegidos = [MODELO, BASE / 'experimentos/v03_01/particiones.json', BASE / 'parametros.py',
                  BASE / 'personalizacion.py', BASE / 'datos/ejemplos.csv',
                  BASE / 'datos/desafio_independiente.csv', BASE / 'datos/desafio_v04.csv',
                  BASE / 'contexto.py', BASE / 'integracion.py', BASE / 'diagnostico_whisper.py',
                  BASE / 'datos/contexto_natural.csv', BASE / 'datos/contexto_adversarial.csv',
                  SALIDA / 'integracion_anterior.py']
    protegidos += [BASE.parent / nombre for nombre in ('main.py', 'interfaz.py', 'whisper_control.py',
                    'recordatorios.py', 'persistencia.py', 'preferencias.py', 'gemini_control.py', 'alarmas.py', 'spotify_control.py')
                   if (BASE.parent / nombre).is_file()]
    hashes = {str(p.relative_to(BASE.parent)): hash_archivo(p) for p in protegidos}
    with (SALIDA / 'congelacion.json').open('x', encoding='utf-8') as archivo:
        json.dump(dict(hashes=hashes, modelo='v03_01/lr_caracteres_original.joblib',
                       nota='Mismo modelo y umbrales. Reglas y desafíos congelados antes de consultar resultados nuevos.'), archivo, indent=2)
    informe = dict(activado=False, modelo_reemplazado=False, conjuntos={}, hashes=hashes)
    for nombre, filas in conjuntos.items():
        a, b = medir(anterior, filas), medir(nuevo, filas)
        mejoras, regresiones = [], []
        for antes, despues in zip(a['detalles'], b['detalles']):
            esperado = antes['esperado']
            def correcto(caso):
                r = caso['resultado']
                return (r['estado'] == 'propuesta' and r.get('intencion') == caso['intencion']) if esperado == 'propuesta' else r['estado'] != 'propuesta'
            par = dict(texto=antes['texto'], esperado=esperado, antes=antes['resultado'], despues=despues['resultado'])
            if not correcto(antes) and correcto(despues):
                mejoras.append(par)
            if correcto(antes) and not correcto(despues):
                regresiones.append(par)
        informe['conjuntos'][nombre] = dict(antes=a, despues=b, mejoras=mejoras, regresiones=regresiones)
    if hashes != {str(p.relative_to(BASE.parent)): hash_archivo(p) for p in protegidos}:
        raise RuntimeError('Los archivos cambiaron durante la evaluación.')
    with (SALIDA / 'informe.json').open('x', encoding='utf-8') as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    resumen = []
    for nombre, r in informe['conjuntos'].items():
        resumen.append(dict(conjunto=nombre, antes={k: r['antes']['metricas'][k] for k in
                       ('cobertura_conocidas', 'precision_aceptadas', 'rechazo_desconocidas', 'aceptaciones_erroneas_total')},
                       despues={k: r['despues']['metricas'][k] for k in
                       ('cobertura_conocidas', 'precision_aceptadas', 'rechazo_desconocidas', 'aceptaciones_erroneas_total')},
                       mejoras=len(r['mejoras']), regresiones=len(r['regresiones']),
                       incompletas_antes=r['antes']['incompletas_propuestas'], incompletas_despues=r['despues']['incompletas_propuestas']))
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return informe


if __name__ == '__main__':
    ejecutar()
