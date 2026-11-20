"""Envolvente visual sin audio, dispositivos, hilos propios ni temporizadores.

QML llama advance desde su único reloj activo. Un productor futuro puede emitir
externalLevel desde otro hilo: la conexión encolada entrega en el hilo gráfico.
"""
from bisect import bisect_right
import math
from numbers import Real
import random

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt, QThread
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'EVABrainV53'
QML_IMPORT_MAJOR_VERSION = 1


def normalized(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError('El nivel debe ser un número real')
    if isinstance(value, int):
        return float(min(1, max(0, value)))  # Incluso enteros mayores que un float.
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('El nivel debe ser finito')
    return min(1.0, max(0.0, value))


class DemoEnvelope:
    """Frases y sílabas precalculadas; misma semilla, misma secuencia larga."""
    def __init__(self, seed=513):
        rng = random.Random(seed)
        self.pulses = []
        cursor = .25
        for _ in range(96):
            phrase_strength = rng.uniform(.45, 1.0)
            for _ in range(rng.randint(3, 9)):
                duration = rng.uniform(.13, .36)
                self.pulses.append((cursor, duration, phrase_strength*rng.uniform(.55, 1.0)))
                cursor += duration + rng.uniform(.025, .10)
            cursor += rng.uniform(.35, 1.05)
        self.duration = cursor
        self.starts = [pulse[0] for pulse in self.pulses]

    def level_at(self, seconds):
        position = seconds % self.duration
        index = bisect_right(self.starts, position)-1
        if index < 0:
            return 0.0
        start, duration, strength = self.pulses[index]
        phase = (position-start)/duration
        return strength*math.sin(math.pi*phase)**2 if 0 <= phase <= 1 else 0.0


@QmlElement
class VoiceReactivity(QObject):
    levelsChanged = Signal()
    settingsChanged = Signal()
    suspendedChanged = Signal()
    externalLevel = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.demo = DemoEnvelope()
        self.demo_time = 0.0
        self._raw = self._smoothed = self._external = 0.0
        self._blend = 0.0
        self._enabled = True
        self._suspended = False
        self._source = 'DEMO'
        self._intensity = .65
        self._jump = 1.0
        self._external_age = 0.0
        self.attack_seconds = .045
        self.release_seconds = .18
        self.external_timeout = .35
        self.externalLevel.connect(self.set_speech_level, Qt.ConnectionType.QueuedConnection)

    speechLevel = Property(float, lambda self: self._raw, notify=levelsChanged)
    speechLevelSmoothed = Property(float, lambda self: self._smoothed, notify=levelsChanged)
    reactivityBlend = Property(float, lambda self: self._blend, notify=levelsChanged)

    def set_enabled(self, value):
        if self._enabled != value:
            self._enabled = value
            self.settingsChanged.emit()

    enabled = Property(bool, lambda self: self._enabled, set_enabled, notify=settingsChanged)

    def set_source(self, value):
        if value in ('DEMO', 'EXTERNAL') and value != self._source:
            self._source = value
            self._external = 0.0
            self.settingsChanged.emit()

    source = Property(str, lambda self: self._source, set_source, notify=settingsChanged)

    def set_intensity(self, value):
        try:
            value = normalized(value)
        except (TypeError, ValueError):
            return
        if value != self._intensity:
            self._intensity = value
            self.settingsChanged.emit()

    demoIntensity = Property(float, lambda self: self._intensity, set_intensity, notify=settingsChanged)

    def set_jump(self, value):
        try:
            value = normalized(value/2)*2
        except (TypeError, ValueError, OverflowError):
            return
        if value != self._jump:
            self._jump = value
            self.settingsChanged.emit()

    speechJumpStrength = Property(float, lambda self: self._jump, set_jump, notify=settingsChanged)

    def set_suspended(self, value):
        if value != self._suspended:
            self._suspended = value
            # Congelar el valor visual, pero no retener una entrada externa vieja.
            self._external = 0.0
            self._external_age = 0.0
            self.suspendedChanged.emit()

    suspended = Property(bool, lambda self: self._suspended, set_suspended, notify=suspendedChanged)

    @Slot('QVariant', result=bool)
    def set_speech_level(self, value):
        """Entrada EXTERNAL: True si válida; usar externalLevel.emit en un worker."""
        if QThread.currentThread() != self.thread():
            return False
        try:
            value = normalized(value)
        except (TypeError, ValueError):
            return False
        if not self._suspended:
            self._external = value
            self._external_age = 0.0
        return True

    @Slot(float, bool)
    def advance(self, delta, speaking):
        if self._suspended or not math.isfinite(delta) or delta <= 0:
            return
        dt = min(delta, .08)  # No recuperar tiempo perdido tras una suspensión.
        self._external_age += dt
        target = 0.0
        if speaking and self._enabled:
            if self._source == 'DEMO':
                self.demo_time += dt
                target = self.demo.level_at(self.demo_time)*self._intensity
            elif self._external_age <= self.external_timeout:
                target = self._external
        else:
            self._external = 0.0
        tau = self.attack_seconds if target > self._smoothed else self.release_seconds
        value = self._smoothed + (target-self._smoothed)*(-math.expm1(-dt/tau))
        value = min(1.0, max(0.0, value))
        if target == 0 and value < .0001:
            value = 0.0
        blend_target = 1.0 if speaking and self._enabled else 0.0
        blend = self._blend + (blend_target-self._blend)*(-math.expm1(-dt/.12))
        if blend_target == 0 and blend < .0001:
            blend = 0.0
        if target != self._raw or value != self._smoothed or blend != self._blend:
            self._raw, self._smoothed = target, value
            self._blend = blend
            self.levelsChanged.emit()  # Como máximo una notificación por frame.

    @Slot()
    def stop(self):
        self.set_suspended(True)
        self._raw = self._smoothed = self._external = 0.0
        self._blend = 0.0
        self.levelsChanged.emit()
