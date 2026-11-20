"""Validación nativa de la máscara GPU, cobertura, estados y suspensión."""
import hashlib
import json
from pathlib import Path
import sys
import traceback
from PySide6.QtCore import QObject, QTimer, QUrl, Qt, QMetaObject, Q_ARG, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QSurfaceFormat, QVector4D
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick3D import QQuick3D
from PySide6.QtQuickControls2 import QQuickStyle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import geometry
from asset_checks import validate_assets


def main():
    validate_assets()
    QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat())
    app = QGuiApplication([])
    QQuickStyle.setStyle('Basic')
    logs = []
    qInstallMessageHandler(lambda kind,context,message: logs.append(message))
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(ROOT/'qml/Main.qml')))
    assert engine.rootObjects()
    w = engine.rootObjects()[0]
    w.resize(1280,760)
    rain = w.findChild(QObject,'matrixBackground')
    view = w.findChild(QObject,'brainViewport')
    circuit = w.findChild(QObject,'circuitMaterial')
    output = ROOT/'previews'
    output.mkdir(parents=True, exist_ok=True)
    report = dict(checks=[], errors=[], states={})
    timer = QTimer(app)
    timer.setSingleShot(True)

    def mode(name):
        assert QMetaObject.invokeMethod(w,'selectMode',Qt.ConnectionType.DirectConnection,Q_ARG('QVariant',name))

    def capture(name):
        grab = w.contentItem().grabToImage()
        ready = []
        def complete(): ready.append(grab.image())
        grab.ready.connect(complete)
        for _ in range(100):
            if ready: break
            yield 20
        grab.ready.disconnect(complete)
        assert ready and not ready[0].isNull()
        assert ready[0].save(str(output/(name+'.png')))
        return ready[0]

    def hashes():
        return [hashlib.sha256(bytes(g.vertexData())).hexdigest() for g in w.findChildren(geometry.NeuralGeometry)]

    def check_projection():
        center, radius = rain.property('exclusionCenter'), rain.property('exclusionRadius')
        assert abs(center.x()-(view.x()+view.width()/2)) < .01
        assert abs(center.y()-(view.y()+view.height()/2)) < .01
        assert radius.x() > 40 and radius.y() > 40
        return radius.x()

    def alpha_counts(picture):
        small = picture.scaled(w.width(),w.height())
        center, radius = rain.property('exclusionCenter'), rain.property('exclusionRadius')
        inside = outside = center_pixels = ink_pixels = 0
        regions = {'left':0,'right':0,'top':0,'bottom':0}
        for y in range(0,small.height(),2):
            for x in range(0,small.width(),2):
                d = ((x-center.x())/radius.x())**2+((y-center.y())/radius.y())**2
                a = small.pixelColor(x,y).alpha()
                if d < .95**2:
                    inside += a
                    center_pixels += 1
                elif d > 1.22**2:
                    outside += 1
                    if a > 5:
                        ink_pixels += 1
                        if x < small.width()*.25: regions['left'] += 1
                        if x > small.width()*.75: regions['right'] += 1
                        if y < small.height()*.16: regions['top'] += 1
                        if y > small.height()*.84: regions['bottom'] += 1
        return dict(inside_alpha_sum=inside,center_pixels=center_pixels,ink_pixels=ink_pixels,
                    outside_pixels=outside,regions=regions)

    def scenario():
        yield 1800
        initial = hashes()
        for state in ('LISTA','ESCUCHANDO','PROCESANDO','HABLANDO','ACLARACIÓN','ERROR','STANDBY'):
            mode(state); yield 1150
            assert circuit.property('uTint') == w.property('tint')
            assert rain.property('stateTint') == w.property('accent')
            assert hashes() == initial
            check_projection()
            report['states'][state] = w.property('accent').name()
            yield from capture('state-'+state)
        mode('LISTA'); yield 1200
        w.setProperty('cameraDistance',560); yield 400
        near = check_projection()
        yield from capture('zoom-near')
        w.setProperty('cameraDistance',800); yield 400
        far = check_projection()
        assert near > far*1.3
        yield from capture('zoom-far')
        w.setProperty('cameraDistance',600)
        w.resize(1400,820); w.setProperty('showPanel',True); yield 1000
        check_projection()
        assert rain.property('panelRect').z() > 0
        yield from capture('panel-wide')
        w.resize(860,640); yield 700
        check_projection()
        yield from capture('compact-panel')
        w.setProperty('showPanel',False); yield 200
        yield from capture('compact')
        w.setProperty('gentleMotion',True); yield 200
        start = w.property('elapsed'); yield 600
        assert .1 < w.property('elapsed')-start < .4
        w.setProperty('reducedMotion',True); yield 150
        frozen = (w.property('elapsed'),rain.property('sceneTime'))
        yield 500
        assert frozen == (w.property('elapsed'),rain.property('sceneTime'))
        w.setProperty('reducedMotion',False)
        w.showMinimized(); yield 300
        frozen = (w.property('elapsed'),rain.property('sceneTime'))
        yield 600
        assert frozen == (w.property('elapsed'),rain.property('sceneTime'))
        assert not w.findChild(QObject,'performanceMonitor').timer.isActive()
        w.showNormal(); w.resize(1280,760)
        w.setProperty('gentleMotion',False); yield 500
        w.setProperty('qualityMode','REDUCIDA'); w.setProperty('lowQuality',True); yield 400
        yield from capture('low-full')
        w.setProperty('qualityMode','ALTA'); w.setProperty('lowQuality',False); yield 400
        report['checks'].append('Siete estados, recursos, voz heredada, zoom, panel, compacto, movimiento suave, pausa y minimizar')
        # Aislar solo la lluvia para medir transparencia verdadera, sin cerebro ni estrellas.
        w.setProperty('reducedMotion',True)
        for item in w.contentItem().childItems():
            if item != rain: item.setVisible(False)
        rain.setProperty('quietRect',QVector4D(0,0,0,0))
        rain.setProperty('panelRect',QVector4D(0,0,0,0))
        w.setProperty('elapsed',20.0); yield 100
        high = yield from capture('matrix-isolated-high')
        counts = alpha_counts(high)
        assert counts['inside_alpha_sum'] == 0, counts
        assert all(n > 100 for n in counts['regions'].values()), counts
        rain.setProperty('maskEnabled',0.0); yield 100
        unmasked = yield from capture('matrix-unmasked-control')
        assert alpha_counts(unmasked)['inside_alpha_sum'] > 10000
        rain.setProperty('maskEnabled',1.0)
        w.setProperty('elapsed',20.2); yield 100
        moved = yield from capture('matrix-motion-200ms')
        a, b = high.scaledToWidth(640), moved.scaledToWidth(640)
        changed = sum(abs(a.pixelColor(x,y).alpha()-b.pixelColor(x,y).alpha()) > 10
                      for y in range(a.height()) for x in range(a.width()))
        assert changed > 500
        w.setProperty('elapsed',20.0)
        w.setProperty('lowQuality',True); yield 200
        low = yield from capture('matrix-isolated-low')
        low_counts = alpha_counts(low)
        assert low_counts['inside_alpha_sum'] == 0
        assert all(n > 50 for n in low_counts['regions'].values())
        assert low_counts['ink_pixels'] < counts['ink_pixels']*.85
        report['gpu'] = dict(high=counts,low=low_counts,changed_pixels_200ms=changed)
        report['checks'].append('GPU: exclusión transparente, cobertura en cuatro regiones, movimiento y menor densidad en reducida')
        assert not logs, logs
        w.close()

    steps = scenario()
    def step():
        try: timer.start(next(steps))
        except StopIteration: w.close()
        except Exception:
            report['errors'].append(traceback.format_exc()); w.close()
    timer.timeout.connect(step)
    app.aboutToQuit.connect(timer.stop)
    step(); app.exec()
    assert not timer.isActive() and not w.findChild(QObject,'performanceMonitor').timer.isActive()
    assert w.findChild(QObject,'voiceReactivity').property('suspended')
    report['qt_messages'] = logs
    report['result'] = 'PASS' if not logs and not report['errors'] else 'FAIL'
    (output/'matrix-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    del engine
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
