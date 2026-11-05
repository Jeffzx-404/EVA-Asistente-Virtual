"""Medición aislada en Windows: sin voz, interfaz, red ni datos personales."""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import time


def memoria():
    if os.name != 'nt':
        return {'actual_mib': None, 'pico_mib': None}
    import ctypes
    from ctypes import wintypes

    class Contadores(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('fallos', wintypes.DWORD)] + [
            (campo, ctypes.c_size_t) for campo in ('pico', 'actual', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6')]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    obtener = kernel.K32GetProcessMemoryInfo
    obtener.argtypes = [wintypes.HANDLE, ctypes.POINTER(Contadores), wintypes.DWORD]
    obtener.restype = wintypes.BOOL
    datos = Contadores()
    datos.cb = ctypes.sizeof(datos)
    if not obtener(kernel.GetCurrentProcess(), ctypes.byref(datos), datos.cb):
        raise OSError('No se pudo medir la memoria del proceso.')
    return {'actual_mib': datos.actual / 1048576, 'pico_mib': datos.pico / 1048576}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--repeticiones', type=int, default=500)
    args = parser.parse_args()
    if args.repeticiones < 20:
        parser.error('Se requieren al menos 20 repeticiones.')
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[variable] = '1'
    inicial = memoria()
    inicio = time.perf_counter()
    from .integracion import InterpreteLocal
    motor = InterpreteLocal(args.modelo)
    carga = time.perf_counter() - inicio
    frases = ('Dime la hora por favor', 'Abre la calculadora', 'No pauses la música',
              'Recuérdame revisar el horno en veinte minutos', 'Traduce una frase al coreano')
    for i in range(20):
        motor.proponer(frases[i % len(frases)], comando_local_atendido=False)
    duraciones = []
    for i in range(args.repeticiones):
        inicio = time.perf_counter()
        motor.proponer(frases[i % len(frases)], comando_local_atendido=False)
        duraciones.append((time.perf_counter() - inicio) * 1000)
    resultado = {'python': platform.python_version(), 'plataforma': platform.system(),
                 'arquitectura': platform.machine(), 'procesadores_logicos': os.cpu_count(),
                 'hilos_blas': 1, 'repeticiones': args.repeticiones,
                 'modelo': args.modelo.name, 'artefacto_bytes': args.modelo.stat().st_size,
                 'memoria_inicial': inicial, 'memoria_final': memoria(),
                 'segundos_importacion_y_carga': carga,
                 'inferencia_ms_mediana': statistics.median(duraciones),
                 'inferencia_ms_p95': sorted(duraciones)[int(.95 * (len(duraciones) - 1))],
                 'inferencia_ms_max': max(duraciones),
                 'alcance': 'Intérprete aislado, 20 calentamientos, mezcla 4 consultas al modelo y 1 rechazo por reglas. Sin Whisper/UI.'}
    # Archivo nuevo para no sobrescribir otras mediciones.
    with args.salida.open('x', encoding='utf-8') as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
