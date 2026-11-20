"""Decisión conservadora sobre ventanas reales de 5 s; sin dependencias Qt."""
class QualityPolicy:
    def __init__(self):
        self.bad = self.good = 0
        self.last_change = -1000.0

    def observe(self, fps, p95_ms, now, low):
        self.bad = self.bad+1 if fps < 48 or p95_ms > 27 else 0
        self.good = self.good+1 if fps > 57 and p95_ms < 20 else 0
        if now-self.last_change < 45:
            return None
        decision = True if not low and self.bad >= 2 else False if low and self.good >= 6 else None
        if decision is not None:
            self.last_change = now
            self.bad = self.good = 0
        return decision
