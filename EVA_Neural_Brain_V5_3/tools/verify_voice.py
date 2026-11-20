"""Pruebas de señal y contrato de entrada; no abre dispositivos de audio."""
import json
import math
from pathlib import Path
import sys
import threading
from PySide6.QtCore import QCoreApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from voice_reactivity import DemoEnvelope, VoiceReactivity


def main():
    app = QCoreApplication([])
    a, b = DemoEnvelope(), DemoEnvelope()
    samples = [a.level_at(i/120) for i in range(120*30)]
    assert samples == [b.level_at(i/120) for i in range(120*30)]
    assert min(samples) == 0 and .5 < max(samples) <= 1
    assert sum(v == 0 for v in samples) > len(samples)*.15
    assert len({round(p[1], 2) for p in a.pulses}) > 15
    voice = VoiceReactivity()
    voice.source = 'EXTERNAL'
    for invalid in (None, True, False, '0.5', [], {}, float('nan'), float('inf'), -float('inf')):
        assert not voice.set_speech_level(invalid), repr(invalid)
    assert voice.set_speech_level(-3)
    assert voice.set_speech_level(-(10**1000))
    voice.advance(.02, True)
    assert voice.speechLevel == 0
    assert voice.set_speech_level(3)
    assert voice.set_speech_level(10**1000)
    voice.advance(.02, True)
    assert voice.speechLevel == 1 and 0 < voice.speechLevelSmoothed < 1
    assert voice.set_speech_level(0)
    previous = voice.speechLevelSmoothed
    voice.advance(.02, True)
    assert 0 < voice.speechLevelSmoothed < previous

    def response(rate):
        v = VoiceReactivity()
        v.source = 'EXTERNAL'
        for _ in range(rate):
            v.set_speech_level(.8)
            v.advance(1/rate, True)
        peak = v.speechLevelSmoothed
        for _ in range(rate):
            v.set_speech_level(0)
            v.advance(1/rate, True)
        return peak, v.speechLevelSmoothed

    values = [response(rate) for rate in (30, 60, 120)]
    assert max(x[0] for x in values)-min(x[0] for x in values) < 1e-10
    assert max(x[1] for x in values)-min(x[1] for x in values) < 1e-10
    assert abs(values[0][1]-.8*math.exp(-1/.18)) < 1e-8
    voice.suspended = True
    frozen = (voice.speechLevel, voice.speechLevelSmoothed, voice.demo_time)
    for _ in range(120):
        voice.set_speech_level(1)
        voice.advance(.016, True)
    assert frozen == (voice.speechLevel, voice.speechLevelSmoothed, voice.demo_time)
    voice.suspended = False
    voice.advance(.016, True)
    assert voice.speechLevel == 0
    results = []
    def worker():
        results.append(voice.set_speech_level(.9))
        voice.externalLevel.emit(.6)
    thread = threading.Thread(target=worker)
    thread.start(); thread.join()
    assert results == [False]
    app.processEvents()
    voice.advance(.016, True)
    assert voice.speechLevel == .6
    for _ in range(60):
        voice.advance(1/60, True)
    assert voice.speechLevel == 0  # timeout evita energía externa pegada.
    for _ in range(120):
        voice.advance(1/60, False)
    assert voice.speechLevelSmoothed == 0 and voice.reactivityBlend == 0
    voice.stop()
    assert voice.suspended and voice.speechLevelSmoothed == 0
    report = dict(result='PASS', demo_peak=max(samples), demo_duration=a.duration,
        silence_fraction=sum(v == 0 for v in samples)/len(samples),
        fps_independence=values, queued_worker=True, suspension=True,
        invalid_inputs_rejected=True, clamp=True, external_timeout=True)
    (ROOT/'previews/voice/signal-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
