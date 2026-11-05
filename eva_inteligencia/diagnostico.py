"""Consola independiente: interpretar, enseñar, consultar y borrar asociaciones.

No inicia EVA, no activa acciones y no guarda conversaciones.
"""
import argparse
import json
from pathlib import Path
from persistencia import ErrorPersistencia
from .personalizacion import ComandosPersonales


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    tareas = parser.add_subparsers(dest='tarea', required=True)
    interpretar = tareas.add_parser('interpretar')
    interpretar.add_argument('texto')
    interpretar.add_argument('--modelo', type=Path, required=True)
    ensenar = tareas.add_parser('ensenar')
    ensenar.add_argument('expresion', help='Cuando diga modo estudio, abre la calculadora')
    tareas.add_parser('listar')
    eliminar = tareas.add_parser('eliminar')
    eliminar.add_argument('expresion')
    args = parser.parse_args()
    servicio = ComandosPersonales()
    try:
        if args.tarea == 'interpretar':
            from .integracion import InterpreteLocal
            resultado = InterpreteLocal(args.modelo, servicio).proponer(args.texto, comando_local_atendido=False)
        elif args.tarea == 'listar':
            resultado = servicio.consultar()
        else:
            propuesta = (servicio.proponer(args.expresion) if args.tarea == 'ensenar'
                         else servicio.proponer_eliminacion(args.expresion))
            print(propuesta['pregunta'])
            aceptado = input('Escribe sí para confirmar; cualquier otra respuesta cancela: ').strip().casefold() in ('sí', 'si')
            resultado = {'guardado': servicio.confirmar(propuesta['token'], aceptado)}
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except (ValueError, OSError, ErrorPersistencia) as error:
        print('No se completó la operación:', error)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nOperación cancelada; no se guardó la propuesta.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
