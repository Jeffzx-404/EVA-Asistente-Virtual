"""Lanzador independiente. Nunca importa módulos del asistente real."""
import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description='EVA Neural Brain V5.3 — demo independiente')
    parser.add_argument('--low', action='store_true', help='Menor resolución, malla y efectos')
    parser.add_argument('--auto', action='store_true', help='Calidad automática con histéresis')
    parser.add_argument('--gentle', action='store_true', help='Movimiento suave y actualización limitada')
    parser.add_argument('--panel', action='store_true', help='Abrir los paneles demostrativos')
    parser.add_argument('--voice-intensity', type=float, default=.65, help='Intensidad de voz sintética, de 0 a 1')
    parser.add_argument('--no-voice', action='store_true', help='Desactivar la reactividad de voz')
    parser.add_argument('--capture', type=Path, help='Guardar una captura del prototipo (PNG) y cerrar')
    parser.add_argument('--anatomy', action='store_true', help='Inspeccionar la superficie sin efectos')
    parser.add_argument('--state', default='LISTA', choices=('LISTA','ESCUCHANDO','PROCESANDO','HABLANDO','ACLARACIÓN','ERROR','STANDBY','IDLE','LISTENING','PROCESSING','SPEAKING'), help='Estado inicial de demostración')
    parser.add_argument('--seconds', type=float, default=5, help='Segundos antes de la captura')
    args = parser.parse_args()
    if not 0 <= args.voice_intensity <= 1:
        parser.error('--voice-intensity debe ser finita y estar entre 0 y 1')

    from PySide6.QtCore import QObject, QTimer, QUrl, QMetaObject, Qt, Q_ARG
    from PySide6.QtGui import QGuiApplication, QSurfaceFormat
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick3D import QQuick3D
    from PySide6.QtQuickControls2 import QQuickStyle
    import geometry  # Registra EVABrainV53 antes de cargar QML.

    QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat())
    app = QGuiApplication(sys.argv[:1])
    QQuickStyle.setStyle('Basic')
    app.setApplicationName('EVA Neural Brain V5.3')
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parent / 'qml' / 'Main.qml')))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    voice = window.findChild(QObject, 'voiceReactivity')
    voice.setProperty('demoIntensity', args.voice_intensity)
    voice.setProperty('enabled', not args.no_voice)
    window.setProperty('lowQuality', args.low)
    window.setProperty('qualityMode', 'AUTOMÁTICA' if args.auto else 'REDUCIDA' if args.low else 'ALTA')
    window.setProperty('gentleMotion', args.gentle)
    window.setProperty('showPanel', args.panel)
    window.setProperty('anatomyView', args.anatomy)
    QMetaObject.invokeMethod(window, 'selectMode', Qt.ConnectionType.DirectConnection, Q_ARG('QVariant', args.state))
    area = app.primaryScreen().availableGeometry()
    window.resize(min(1400, area.width()-50), min(820, area.height()-60))
    timer = QTimer(app)
    timer.setSingleShot(True)
    errors = []
    if args.capture:
        def capture():
            args.capture.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            if image.isNull() or not image.save(str(args.capture)):
                errors.append('No se pudo guardar la captura')
            else:
                print(f'Captura: {args.capture}', flush=True)
            window.close()
        timer.timeout.connect(capture)
        timer.start(max(1000, int(args.seconds*1000)))
    app.aboutToQuit.connect(timer.stop)
    code = app.exec()
    del engine
    return 1 if errors else code


if __name__ == '__main__':
    raise SystemExit(main())
