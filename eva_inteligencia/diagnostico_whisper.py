"""Diagnóstico sin ejecutores: texto, WAV o micrófono activado explícitamente.

No guarda audio/transcripciones ni descarga modelos. La medición
conjunta sólo persiste métricas si se indica --salida-metricas.
"""
import argparse
import io
import json
import os
from pathlib import Path
import sys
import time
import wave


def diagnosticar(motor, texto):
    from .entrenamiento import puntuar, decidir, DESCONOCIDO
    from .seguridad import revisar_seguridad
    from .texto import normalizar
    problema = revisar_seguridad(texto)
    candidato, datos, fallos = None, {}, []
    if isinstance(texto, str) and texto.strip() and len(texto) <= 1000:
        p = motor.paquete
        scores = puntuar(p['modelo'], [normalizar(texto)], p['referencias'])
        candidato = str(scores[0][0])
        u = p['umbrales'].get('por_intencion', {}).get(candidato, p['umbrales'])
        datos = dict(score=float(scores[1][0]), margen=float(scores[2][0]), similitud=float(scores[3][0]),
                     umbrales={k: u[k] for k in ('score', 'margen', 'similitud')})
        fallos = [k for k in ('score', 'margen', 'similitud') if datos[k] < u[k]]
        if candidato == DESCONOCIDO:
            fallos.append('clase_fuera_de_alcance')
    resultado = motor.proponer(texto, comando_local_atendido=False)
    aceptada = resultado['estado'] == 'propuesta'
    motivo = (resultado.get('motivo') or problema or ('No supera: ' + ', '.join(fallos) if fallos else None)
              or resultado.get('pregunta') or resultado.get('mensaje')
              or 'Supera los umbrales y la validación de parámetros; sólo propuesta de diagnóstico.')
    estado = ('aceptada' if aceptada else 'aclaracion' if resultado['estado'] == 'aclaracion'
              else 'error' if resultado['estado'] == 'error' else 'desconocida')
    return dict(transcripcion=texto, estado=estado, intencion_candidata=candidato, aceptada=aceptada, motivo=motivo,
                parametros=resultado.get('parametros'), resultado=resultado, puntuaciones=datos,
                intenciones_posibles=resultado.get('intenciones_posibles', []),
                por_resolver=resultado.get('por_resolver', []), ejecutable=False)


def cargar_small_local():
    from faster_whisper import WhisperModel
    from faster_whisper.utils import download_model
    from whisper_control import MODELO_WHISPER
    # Mismos parámetros de carga que EVA; local_files_only impide descargar.
    cache = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'EVA' / 'whisper'
    ruta = Path(download_model(MODELO_WHISPER, cache_dir=str(cache), local_files_only=True, use_auth_token=False))
    if not all((ruta / nombre).is_file() for nombre in ('model.bin', 'config.json', 'tokenizer.json')):
        raise RuntimeError('Whisper Small no está completo en la caché local. No se descargó nada.')
    return WhisperModel(str(ruta), device='cpu', compute_type='int8', num_workers=1, local_files_only=True)


def diagnosticar_wav(motor, ruta):
    ruta = Path(ruta)
    if ruta.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('El WAV supera 64 MiB. Elige una grabación breve; no se recorta automáticamente.')
    wav = ruta.read_bytes()
    with wave.open(io.BytesIO(wav), 'rb') as archivo:
        if archivo.getnframes() == 0:
            raise ValueError('La grabación está vacía.')
    from whisper_control import _transcribir_wav
    modelo = cargar_small_local()
    inicio = time.perf_counter()
    texto = _transcribir_wav(modelo, wav)  # Reutiliza TODOS los parámetros actuales de EVA.
    resultado = diagnosticar(motor, texto)
    resultado['transcripcion'] = texto  # Sólo consola, para comprobar lo que oyó Whisper.
    resultado['transcripcion_segundos'] = time.perf_counter() - inicio
    return resultado


def capturar_microfono(dispositivo=None):
    """Una frase en memoria; misma configuración de captura que EVA.

    Se llama sólo después de Enter en el modo interactivo. Ctrl+C cancela.
    No hay escucha de fondo, límite que trunque frases ni fallback de red.
    """
    import speech_recognition as sr
    from whisper_control import configurar_captura
    reconocedor = sr.Recognizer()
    configurar_captura(reconocedor)
    with sr.Microphone(device_index=dispositivo) as fuente:
        print('Calibrando ruido durante un segundo; espera para hablar.', flush=True)
        reconocedor.adjust_for_ambient_noise(fuente, duration=1)
        print('Habla ahora. Haz una pausa al terminar. Ctrl+C cancela.', flush=True)
        audio = reconocedor.listen(fuente)
    # Mismo formato que ControlWhisper.transcribir; se cierra el micrófono antes de inferir.
    return audio.get_wav_data(convert_rate=16000, convert_width=2)


def sesion_microfono(motor, dispositivo=None):
    """Carga Small una vez; cada captura requiere que la persona pulse Enter."""
    from whisper_control import _transcribir_wav
    print('Diagnóstico local: no se ejecutan acciones ni se guardan grabaciones o textos.')
    print('Cargando Whisper Small desde la caché local...', flush=True)
    small = cargar_small_local()
    while True:
        try:
            respuesta = input('Enter para capturar una frase; q y Enter para salir: ').strip().casefold()
            if respuesta == 'q':
                return
            if respuesta:
                print('Pulsa sólo Enter para capturar, o q para salir.')
                continue
            wav = capturar_microfono(dispositivo)
            inicio = time.perf_counter()
            texto = _transcribir_wav(small, wav)
            del wav
            resultado = diagnosticar(motor, texto)
            resultado['transcripcion_segundos'] = time.perf_counter() - inicio
            print(json.dumps(resultado, ensure_ascii=False, indent=2), flush=True)
            del texto, resultado
        except (KeyboardInterrupt, EOFError):
            print('\nDiagnóstico cancelado. Micrófono cerrado.')
            return


def medir_conjunto(motor):
    from .medir import memoria
    from interfaz import InterfazEVA
    inicial = memoria()
    vista = InterfazEVA()
    vista.ventana.withdraw()
    try:
        vista.ventana.update()
        con_interfaz = memoria()
        inicio = time.perf_counter()
        whisper = cargar_small_local()
        carga = time.perf_counter() - inicio
        # Audio sintético silencioso: no micrófono ni transcripciones personales.
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as archivo:
            archivo.setnchannels(1)
            archivo.setsampwidth(2)
            archivo.setframerate(16000)
            archivo.writeframes(b'\x00\x00' * 16000 * 2)
        from whisper_control import _transcribir_wav
        inicio = time.perf_counter()
        _transcribir_wav(whisper, buffer.getvalue())
        silencio = time.perf_counter() - inicio
        diagnosticar(motor, 'Dime la hora del equipo')
        vista.ventana.update()
        return dict(interprete=inicial, con_tkinter=con_interfaz, con_small_y_tkinter=memoria(),
                    carga_small_segundos=carga, wav_silencio_segundos=silencio,
                    alcance='Interfaz real oculta, Small CPU/int8 y clasificador en un proceso; 2 s de silencio sintético. Sin main, callbacks de acciones ni audio personal.')
    finally:
        vista._cerrar()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', type=Path, default=Path(__file__).resolve().parent / 'experimentos/v03_01/lr_caracteres_original.joblib')
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument('--wav', type=Path)
    modos.add_argument('--medir-conjunto', action='store_true')
    modos.add_argument('--microfono', action='store_true')
    modos.add_argument('--listar-microfonos', action='store_true')
    parser.add_argument('--dispositivo', type=int, help='Índice opcional del micrófono; por defecto el de Windows.')
    parser.add_argument('--salida-metricas', type=Path)
    args = parser.parse_args()
    if args.salida_metricas and not args.medir_conjunto:
        parser.error('--salida-metricas sólo admite medición conjunta, nunca transcripciones.')
    if args.dispositivo is not None and (not args.microfono or args.dispositivo < 0):
        parser.error('--dispositivo requiere --microfono y un índice no negativo.')
    try:
        if args.listar_microfonos:
            import speech_recognition as sr
            for indice, nombre in enumerate(sr.Microphone.list_microphone_names()):
                print(f'{indice}: {nombre}')
            return 0
        from .integracion import InterpreteLocal
        motor = InterpreteLocal(args.modelo)  # Sin personalización ni lectura de preferencias.
        if args.microfono:
            sesion_microfono(motor, args.dispositivo)
        elif args.medir_conjunto:
            resultado = medir_conjunto(motor)
            if args.salida_metricas:
                with args.salida_metricas.open('x', encoding='utf-8') as archivo:
                    json.dump(resultado, archivo, ensure_ascii=False, indent=2)
            print(json.dumps(resultado, ensure_ascii=False, indent=2))
        elif args.wav:
            print(json.dumps(diagnosticar_wav(motor, args.wav), ensure_ascii=False, indent=2))
        else:
            print('Pega transcripciones de Whisper, una por línea. Ctrl+Z y Enter para salir en Windows. No se guardan.', file=sys.stderr)
            for linea in sys.stdin:
                print(json.dumps(diagnosticar(motor, linea.strip()), ensure_ascii=False, indent=2))
    except (KeyboardInterrupt, EOFError):
        print('\nDiagnóstico cancelado; no se guardó audio ni texto.', file=sys.stderr)
        return 0
    except (ImportError, OSError, ValueError, RuntimeError, AttributeError) as error:
        print('Diagnóstico no completado:', type(error).__name__, file=sys.stderr)
        print('Comprueba Small local, las dependencias, el archivo o los permisos/dispositivo de micrófono de Windows. No se ejecutaron acciones.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
