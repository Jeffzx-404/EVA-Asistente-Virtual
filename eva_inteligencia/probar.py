"""Prueba interactiva del modelo oficial, sin conexión y sin ejecutar órdenes."""
from .integracion import InterpreteLocal
from .diagnostico_whisper import diagnosticar


def main():
    motor = InterpreteLocal()
    print('Probador de intenciones de EVA (escribe salir para finalizar).')
    print('No se ejecutarán órdenes ni se crearán recordatorios.')
    while True:
        try:
            texto = input('\nTú: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nFin de prueba.')
            break
        if texto.lower() in {'salir', 'exit'}:
            break
        print('Resultado:', diagnosticar(motor, texto))


if __name__ == '__main__':
    main()
