"""Compara HABLANDO antes/después; una ventana y ningún capturador concurrente."""
import argparse
import json
from pathlib import Path
import statistics
import sys
import time
from PySide6.QtCore import QTimer, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QSurfaceFormat
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick3D import QQuick3D
from PySide6.QtQuickControls2 import QQuickStyle

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', action='store_true')
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    scene = ROOT.parent/'EVA_Neural_Brain_V5_2' if args.before else ROOT
    sys.path.insert(0, str(scene))
    import geometry
    if args.before:
        from verify import memory_mib
    else:
        from asset_checks import memory_mib
    QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat())
    app = QGuiApplication([])
    QQuickStyle.setStyle('Basic')
    logs = []
    qInstallMessageHandler(lambda kind, context, message: logs.append(message))
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(scene/'qml/Main.qml')))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    window.resize(1280, 760)
    window.requestActivate()
    window.setProperty('currentMode', 'HABLANDO')
    # Mantener el mismo viewport para comparar el coste del efecto, sin que la
    # fila nueva de controles reduzca la superficie renderizada de la nueva demo.
    window.setProperty('showControls', False)
    frames, memory, measures = [], [], []
    window.frameSwapped.connect(lambda: frames.append(time.perf_counter()))
    timer = QTimer(app)
    timer.setSingleShot(True)
    sampler = QTimer(app)
    sampler.setInterval(10000)
    sampler.timeout.connect(lambda: memory.append(memory_mib()))
    profiles = iter(('ALTA', 'REDUCIDA', 'AUTOMÁTICA'))
    state = {}

    def select():
        mode = next(profiles, None)
        if mode is None:
            window.close()
            return
        state['mode'] = mode
        window.setProperty('qualityMode', mode)
        window.setProperty('lowQuality', mode == 'REDUCIDA')
        state['phase'] = 'warmup'
        timer.start(2000)

    def step():
        if state['phase'] == 'warmup':
            frames.clear()
            memory.clear()
            state.update(phase='measure', start=time.perf_counter(), cpu=time.process_time())
            timer.start(args.seconds*1000)
            sampler.start()
            return
        sampler.stop()
        duration = time.perf_counter()-state['start']
        intervals = sorted((b-a)*1000 for a, b in zip(frames, frames[1:]))
        measures.append(dict(profile=state['mode'], seconds=round(duration, 2),
            fps=round(len(frames)/duration, 2),
            p95_ms=round(intervals[int(len(intervals)*.95)], 2) if intervals else None,
            median_ms=round(statistics.median(intervals), 2) if intervals else None,
            cpu_one_core=round((time.process_time()-state['cpu'])/duration*100, 2),
            memory_mib=memory_mib(), memory_samples=list(memory),
            low_final=window.property('lowQuality'), exposed=window.isExposed()))
        print(json.dumps(measures[-1]), flush=True)
        select()

    timer.timeout.connect(step)
    app.aboutToQuit.connect(timer.stop)
    app.aboutToQuit.connect(sampler.stop)
    select()
    app.exec()
    passed = len(measures) == 3 and not logs and all(m['fps'] > 15 for m in measures)
    report = dict(result='PASS' if passed else 'FAIL', measurements=measures,
                  qt_messages=logs, size=[1280,760], dpr=window.devicePixelRatio(),
                  scene=str(scene), state='HABLANDO', view='cine')
    name = 'benchmark-before.json' if args.before else 'benchmark-after.json'
    (ROOT/'previews'/name).write_text(json.dumps(report, indent=2), encoding='utf-8')
    del engine
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
