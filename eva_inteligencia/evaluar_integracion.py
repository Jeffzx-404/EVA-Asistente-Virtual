"""Evalúa el adaptador completo sin ejecutores; no cambia umbrales ni modelos."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from .entrenamiento import BASE, DESCONOCIDO, evaluar, leer_corpus
from .integracion import InterpreteLocal
from .motor import MotorIntenciones


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    filas = leer_corpus(BASE / 'datos/desafio_independiente.csv')
    nuevo = InterpreteLocal(args.modelo)
    original = MotorIntenciones(usar_alias=False)
    detalles, predicciones = [], []
    for fila in filas:
        antes = original.clasificar(fila['texto'])
        despues = nuevo.proponer(fila['texto'], comando_local_atendido=False, ahora=datetime(2026, 11, 4, 10))
        predicciones.append(despues.get('intencion') if despues['estado'] == 'propuesta' else DESCONOCIDO)
        detalles.append({**fila, 'original': antes, 'adaptador': despues})
    informe = {'evaluacion': evaluar(filas, predicciones), 'detalles': detalles,
               'advertencia': 'Incluye validaciones deterministas y parámetros: no es una mejora atribuible sólo al modelo.'}
    with args.salida.open('x', encoding='utf-8') as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in informe['evaluacion'].items()
                      if k not in ('por_intencion', 'matriz_confusion', 'errores', 'etiquetas_matriz')}, indent=2))


if __name__ == '__main__':
    main()
