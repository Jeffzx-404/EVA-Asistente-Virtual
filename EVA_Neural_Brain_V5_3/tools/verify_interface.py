"""Regresión de interfaz V5.2: paneles, teclado, transiciones y calidad automática."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from PySide6.QtCore import QObject,QTimer,QUrl,Qt,QPointF,QMetaObject,Q_ARG,qInstallMessageHandler
from PySide6.QtGui import QGuiApplication,QSurfaceFormat
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick3D import QQuick3D
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import geometry


def main():
    QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat())
    app=QGuiApplication([])
    QQuickStyle.setStyle('Basic')
    logs=[]
    qInstallMessageHandler(lambda kind,context,message:logs.append(message))
    engine=QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(ROOT/'qml/Main.qml')))
    assert engine.rootObjects()
    w=engine.rootObjects()[0]
    output=Path(os.environ.get('EVA_DEMO_VERIFY_OUTPUT', ROOT/'previews'))
    output.mkdir(parents=True, exist_ok=True)
    report={'checks':[],'errors':[]}
    timer=QTimer(app);timer.setSingleShot(True)

    def invoke(name,value):
        assert QMetaObject.invokeMethod(w,name,Qt.ConnectionType.DirectConnection,Q_ARG('QVariant',value))

    def find(item,name):
        if item.objectName()==name:return item
        for child in item.childItems():
            match=find(child,name)
            if match is not None:return match

    def click(name):
        item=find(w.contentItem(),name)
        assert item is not None,name
        point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
        QTest.mouseClick(w,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)

    def capture(name):
        assert w.grabWindow().save(str(output/(name+'.png')))

    def hashes():
        return [hashlib.sha256(bytes(g.vertexData())).hexdigest() for g in w.findChildren(geometry.NeuralGeometry)]

    def scenario():
        yield 1500
        initial=hashes()
        for state in ('ESCUCHANDO','PROCESANDO','HABLANDO','LISTA','ERROR','ESCUCHANDO'):
            invoke('selectMode',state)
            yield 100
            weights=[w.property(name+'Motion') for name in ('listening','processing','speaking','standby','waiting','error')]
            assert all(0<=value<=1 for value in weights) and sum(weights)<=1.001
            assert hashes()==initial
        yield 3800
        assert w.property('currentMode')=='ESCUCHANDO','Un timer ERROR anterior cambió el estado'
        report['checks'].append('Transiciones rápidas sin regenerar geometría; ERROR cancelado correctamente')
        click('panelButton');yield 500
        assert w.property('showPanel')
        capture('panel-conversation')
        input_item=find(w.contentItem(),'demoInput');input_item.setProperty('text','Prueba local')
        click('demoSend');yield 200
        assert w.property('currentMode')=='HABLANDO'
        click('demoMic');yield 200
        assert w.property('currentMode')=='ESCUCHANDO'
        panel=w.findChild(QObject,'demoPanel')
        navigation=find(w.contentItem(),'demoNavigation')
        click('demoNavigation');yield 200
        QTest.keyClick(w,Qt.Key.Key_Down);QTest.keyClick(w,Qt.Key.Key_Return);yield 200
        assert panel.property('section')=='Recordatorios'
        for section in ('Alarmas','Configuración','Servicios'):
            panel.setProperty('section',section);yield 100
        capture('panel-services')
        click('closePanel');yield 200
        assert not w.property('showPanel')
        click('qualitySelector');yield 150
        QTest.keyClick(w,Qt.Key.Key_Down);QTest.keyClick(w,Qt.Key.Key_Return);yield 300
        assert w.property('lowQuality')
        invoke('selectQuality','AUTOMÁTICA');yield 100
        monitor=w.findChild(QObject,'performanceMonitor')
        def sample(fps,p95_s):
            now=time.perf_counter();monitor._eligible_before=True
            monitor.start=now-5.1
            count=int(fps*5.1)
            monitor.frames=[now-(count-i)*p95_s for i in range(count)]
            monitor.sample()
        w.setProperty('lowQuality',False)
        sample(35,.029);assert not w.property('lowQuality')
        sample(35,.029);assert w.property('lowQuality')
        monitor.policy.last_change-=46
        for _ in range(6):sample(60,1/60)
        assert not w.property('lowQuality')
        monitor.policy.bad=monitor.policy.good=0;monitor.frames.clear();monitor.start=time.perf_counter()
        monitor._fps=0;monitor._p95=0;monitor.changed.emit()
        report['checks'].append('Calidad automática: recomendaciones conectadas a QML; muestras sintéticas etiquetadas')
        invoke('selectQuality','ALTA')
        click('gentleButton');yield 1300
        assert w.property('gentleMotion')
        t=w.property('elapsed');yield 1000
        assert .2 < w.property('elapsed')-t < .55
        click('pauseButton');yield 200
        t=w.property('elapsed');yield 400
        assert w.property('elapsed')==t and not monitor.timer.isActive()
        click('pauseButton');click('gentleButton');yield 200
        w.showMinimized();yield 300
        t=w.property('elapsed');yield 500
        assert w.property('elapsed')==t and not monitor.timer.isActive()
        w.showNormal();w.resize(860,640);yield 500
        for name in ('pauseButton','panelButton','qualitySelector','state-STANDBY'):
            item=find(w.contentItem(),name);p=item.mapToScene(QPointF(0,0))
            assert p.x()>=0 and p.y()>=0 and p.x()+item.width()<=w.width() and p.y()+item.height()<=w.height(),name
        capture('compact')
        click('panelButton');yield 300;capture('compact-panel');click('closePanel')
        w.showMaximized();yield 500;capture('maximized')
        w.showNormal();w.resize(1400,820);yield 400
        click('cinemaButton');yield 300;capture('cinema')
        QTest.keyClick(w,Qt.Key.Key_Escape);yield 100
        assert w.property('showControls')
        QTest.keyClick(w,Qt.Key.Key_Tab);yield 100
        assert w.activeFocusItem() is not None
        report['checks'].append('Paneles, teclado, compacto, maximizar/restaurar, suave, pausa, minimizar y cine')
        assert not logs,logs
        w.close()

    steps=scenario()
    def step():
        try:timer.start(next(steps))
        except StopIteration:w.close()
        except Exception:
            report['errors'].append(traceback.format_exc());w.close()
    timer.timeout.connect(step)
    app.aboutToQuit.connect(timer.stop)
    step();app.exec()
    monitor=w.findChild(QObject,'performanceMonitor')
    assert not timer.isActive() and not monitor.timer.isActive()
    del engine
    report['qt_messages']=logs
    report['result']='PASS' if not report['errors'] and not logs else 'FAIL'
    (output/'interface-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['result']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
