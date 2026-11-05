"""Regresión sintética antes/después. No captura micrófono ni guarda datos personales."""
import hashlib
import importlib.util
import json

from .evaluar_contexto import BASE, MODELO, leer, medir
from .integracion import InterpreteLocal

SALIDA = BASE / 'experimentos/voz_v01'


def cargar_anterior():
    def modulo(nombre, archivo):
        spec = importlib.util.spec_from_file_location('eva_inteligencia.' + nombre, archivo)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    contexto = modulo('_voz_contexto_anterior', SALIDA / 'anterior/contexto.py')
    integracion = modulo('_voz_integracion_anterior', SALIDA / 'anterior/integracion.py')
    # Aislar las referencias del módulo copiado, sin parchear el adaptador activo.
    integracion.analizar_contexto = contexto.analizar_contexto
    integracion.validar_contexto = contexto.validar_contexto
    return integracion.InterpreteLocal(MODELO)


def ejecutar():
    if (SALIDA / 'informe.json').exists():
        raise FileExistsError('La comparación existente se conserva.')
    anterior, nuevo = cargar_anterior(), InterpreteLocal(MODELO)
    historico = json.loads((BASE / 'experimentos/contexto_v01/informe.json').read_text(encoding='utf-8'))
    archivos = [BASE / 'contexto.py', BASE / 'diagnostico_whisper.py', BASE / 'integracion.py',
                MODELO, BASE / 'personalizacion.py', BASE / 'parametros.py',
                BASE / 'experimentos/v03_01/particiones.json']
    archivos += [BASE.parent / n for n in ('main.py', 'whisper_control.py', 'interfaz.py', 'persistencia.py',
                'preferencias.py', 'recordatorios.py', 'alarmas.py', 'spotify_control.py', 'gemini_control.py')
                 if (BASE.parent / n).is_file()]
    archivos += sorted((SALIDA / 'anterior').glob('*.py'))
    for n in ('desafio_v04.csv', 'contexto_natural.csv', 'contexto_adversarial.csv'):
        archivos.append(BASE / 'datos' / n)
    hashes = {str(p.relative_to(BASE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in archivos}
    with (SALIDA / 'congelacion.json').open('x', encoding='utf-8') as archivo:
        json.dump(dict(hashes=hashes, nota='Conjuntos anteriores de regresión; no son nuevas pruebas ciegas.'), archivo, indent=2)
    informe = dict(modelo_reemplazado=False, acciones_habilitadas=False,
                   voz_real_evaluada=False, conjuntos={}, hashes=hashes)
    for nombre, csv in (('desarrollo_conocido_v04', 'desafio_v04.csv'), ('nuevo_natural', 'contexto_natural.csv'),
                        ('nuevo_adversarial', 'contexto_adversarial.csv')):
        filas = leer(csv)
        a, b = medir(anterior, filas), medir(nuevo, filas)
        if a != historico['conjuntos'][nombre]['despues']:
            raise RuntimeError('El adaptador archivado no reproduce exactamente la evaluación anterior.')
        diferencias = [dict(texto=x['texto'], esperado=x['esperado'], antes=x['resultado'], despues=y['resultado'])
                       for x, y in zip(a['detalles'], b['detalles']) if x['resultado'] != y['resultado']]
        informe['conjuntos'][nombre] = dict(antes=a, despues=b, diferencias=diferencias)
    informe['sin_empeorar_metricas'] = all(
        r['despues']['metricas']['cobertura_conocidas'] >= r['antes']['metricas']['cobertura_conocidas']
        and r['despues']['metricas']['aceptaciones_erroneas_total'] <= r['antes']['metricas']['aceptaciones_erroneas_total']
        and r['despues']['metricas']['rechazo_desconocidas'] >= r['antes']['metricas']['rechazo_desconocidas']
        and r['despues']['incompletas_propuestas'] <= r['antes']['incompletas_propuestas']
        for r in informe['conjuntos'].values())
    if hashes != {str(p.relative_to(BASE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in archivos}:
        raise RuntimeError('Algún archivo cambió durante la comparación.')
    with (SALIDA / 'informe.json').open('x', encoding='utf-8') as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    print('Sin empeorar métricas:', informe['sin_empeorar_metricas'])
    for n, r in informe['conjuntos'].items():
        print(n, json.dumps({momento: {k: r[momento]['metricas'][k] for k in
               ('cobertura_conocidas', 'precision_aceptadas', 'rechazo_desconocidas', 'aceptaciones_erroneas_total')}
               for momento in ('antes', 'despues')}))
    return informe


if __name__ == '__main__':
    ejecutar()
