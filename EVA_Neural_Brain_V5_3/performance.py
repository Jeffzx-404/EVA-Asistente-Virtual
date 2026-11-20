"""Mide frames presentados; no utiliza la velocidad de captura de video."""
import time
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from PySide6.QtQml import QmlElement
from quality_policy import QualityPolicy

QML_IMPORT_NAME = 'EVABrainV53'
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class PerformanceMonitor(QObject):
    changed = Signal()
    recommended = Signal(bool, str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.window = None
        self.frames = []
        self.start = time.perf_counter()
        self.policy = QualityPolicy()
        self._running = False
        self._fps = self._p95 = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.sample)
        self._eligible_before = None

    @Slot(QObject)
    def attach(self,window):
        if self.window is not None:
            return
        self.window = window
        window.frameSwapped.connect(self.frame)

    def frame(self):
        if self._running:
            self.frames.append(time.perf_counter())

    def set_running(self,value):
        if value == self._running:
            return
        self._running = value
        self.frames.clear()
        self.start = time.perf_counter()
        self.policy.bad = self.policy.good = 0
        self.timer.start() if value else self.timer.stop()
        self.changed.emit()

    running = Property(bool,lambda self:self._running,set_running,notify=changed)
    fps = Property(float,lambda self:self._fps,notify=changed)
    p95 = Property(float,lambda self:self._p95,notify=changed)

    @Slot()
    def stop(self):
        self.set_running(False)

    def sample(self):
        if self.window is None:
            return
        now = time.perf_counter()
        # Una ventana no expuesta no aporta una medida válida de carga gráfica.
        # Descartar ese intervalo evita bajar calidad al volver al escritorio.
        if not self.window.isExposed():
            self.frames.clear()
            self.start = now
            self.policy.bad = self.policy.good = 0
            return
        eligible = (not self.window.property('gentleMotion')
                    and self.window.property('currentMode') != 'STANDBY')
        if eligible != self._eligible_before:
            self._eligible_before = eligible
            self.start = now
            self.frames.clear()
            self.policy.bad = self.policy.good = 0
            return
        duration = now-self.start
        if duration < 5 or len(self.frames)<2:
            return
        intervals = sorted((b-a)*1000 for a,b in zip(self.frames,self.frames[1:]))
        self._fps = len(self.frames)/duration
        self._p95 = intervals[int(len(intervals)*.95)]
        self.changed.emit()
        if self.window.property('qualityMode') == 'AUTOMÁTICA' and eligible:
            choice = self.policy.observe(self._fps,self._p95,now,self.window.property('lowQuality'))
            if choice is not None:
                reason = 'Carga sostenida' if choice else 'Recuperación estable; prueba de alta'
                self.recommended.emit(choice,reason)
        else:
            self.policy.bad = self.policy.good = 0
        self.frames.clear()
        self.start = now
