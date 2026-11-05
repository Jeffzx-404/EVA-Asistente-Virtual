"""Prueba interactiva local sin conexión y sin ejecutar órdenes."""
from .motor import MotorIntenciones


def main():
    motor = MotorIntenciones()
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
        print('Resultado:', motor.clasificar(texto))


if __name__ == '__main__':
    main()
