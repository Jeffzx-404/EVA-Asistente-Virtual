"""Regresión de histéresis: ventanas malas aisladas, sostenidas y recuperación."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from quality_policy import QualityPolicy

p = QualityPolicy()
assert p.observe(40,30,5,False) is None
assert p.observe(60,17,10,False) is None  # Una caída no baja calidad.
assert p.observe(40,30,15,False) is None
assert p.observe(40,30,20,False) is True
for now in range(25,65,5):
    assert p.observe(60,17,now,True) is None  # Espera mínima de 45 s.
assert p.observe(60,17,65,True) is False
for now in range(70,110,5):
    assert p.observe(30,40,now,False) is None
assert p.observe(30,40,110,False) is True
q = QualityPolicy()
for now in range(5,100,5):
    assert q.observe(54,22,now,True) is None  # Banda de histéresis.
print('PASS: caída aislada, dos ventanas malas, recuperación, histéresis y cooldown')
