"""Recursos estáticos de GPU. No se reconstruyen mallas durante la animación."""
from array import array
from functools import lru_cache
import json
import math
import random
from pathlib import Path
import struct

from PySide6.QtCore import Property, Signal
from PySide6.QtGui import QVector3D
from PySide6.QtQml import QmlElement
from PySide6.QtQuick3D import QQuick3DGeometry
from performance import PerformanceMonitor  # Registra el monitor QML, sin backend EVA.
from voice_reactivity import VoiceReactivity  # Envolvente visual; no abre audio.

QML_IMPORT_NAME = "EVABrainV53"
QML_IMPORT_MAJOR_VERSION = 1
ASSETS = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=2)
def read_surface(quality):
    raw = (ASSETS / f"brain_{quality}.glb").read_bytes()
    json_length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+json_length])
    binary = raw[28+json_length:]
    def buffer(index):
        view = doc['bufferViews'][index]
        start = view.get('byteOffset', 0)
        return binary[start:start+view['byteLength']]
    values = array('f')
    positions = tuple(struct.iter_unpack('<3f', buffer(0)))
    normals = tuple(struct.iter_unpack('<3f', buffer(1)))
    for position, normal in zip(positions, normals):
        values.extend((*position, *normal))
    return values.tobytes(), buffer(2), doc['accessors'][0]['min'], doc['accessors'][0]['max']


@lru_cache(maxsize=1)
def network():
    return json.loads((ASSETS / 'surface_network.json').read_text(encoding='utf-8'))


@QmlElement
class BrainSurface(QQuick3DGeometry):
    lowQualityChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._low = False
        self._build()

    def get_low(self):
        return self._low

    def set_low(self, value):
        if value != self._low:
            self._low = value
            self._build()
            self.lowQualityChanged.emit()

    lowQuality = Property(bool, get_low, set_low, notify=lowQualityChanged)

    def _build(self):
        vertices, indices, low, high = read_surface('low' if self._low else 'high')
        self.clear()
        self.setVertexData(vertices)
        self.setIndexData(indices)
        self.setStride(24)
        self.setBounds(QVector3D(*low), QVector3D(*high))
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
        sem, typ = QQuick3DGeometry.Attribute.Semantic, QQuick3DGeometry.Attribute.ComponentType
        self.addAttribute(sem.PositionSemantic, 0, typ.F32Type)
        self.addAttribute(sem.NormalSemantic, 12, typ.F32Type)
        self.addAttribute(sem.IndexSemantic, 0, typ.U32Type)
        self.update()


@QmlElement
class NeuralGeometry(QQuick3DGeometry):
    kindChanged = Signal()
    lowQualityChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kind = ''
        self._low = False

    def get_kind(self):
        return self._kind

    def set_kind(self, value):
        if value != self._kind:
            self._kind = value
            self._build()
            self.kindChanged.emit()

    kind = Property(str, get_kind, set_kind, notify=kindChanged)

    def get_low(self):
        return self._low

    def set_low(self, value):
        if value != self._low:
            self._low = value
            if self._kind:
                self._build()
            self.lowQualityChanged.emit()

    lowQuality = Property(bool, get_low, set_low, notify=lowQualityChanged)

    def _build(self):
        data = array('f')
        triangles = False
        def emit(point, u, seed):
            data.extend((*point, u, seed))
        if self._kind in ('filaments', 'innerFilaments'):
            paths = network()['paths']
            if self._kind == 'innerFilaments':
                paths = paths[::9]
            for index, path in enumerate(paths):
                distance = 0.0
                for a, b in zip(path, path[1:]):
                    length = math.dist(a, b)
                    emit(a, distance / 70, index * .618034 % 1)
                    distance += length
                    emit(b, distance / 70, index * .618034 % 1)
        elif self._kind in ('particles', 'shellParticles', 'cosmic'):
            triangles = True
            points = network()['particles']
            if self._kind == 'cosmic':
                # Distribución en volumen; los 180 primeros son idénticos en ambas calidades.
                rng = random.Random(505)
                points = []
                for index in range(180 if self._low else 540):
                    y = rng.uniform(-1, 1)
                    angle = rng.uniform(0, math.tau)
                    # Capas intercaladas: reducida conserva las tres y el mismo prefijo.
                    layer = index % 3
                    radius = rng.uniform(210+layer*45, 250+layer*45)
                    ring = math.sqrt(1-y*y)
                    points.append((radius*ring*math.cos(angle)*1.30, radius*y*.82,
                                   -190+layer*160 + radius*ring*math.sin(angle)*.24))
            elif self._kind == 'shellParticles':
                points = []
                for i in range(240):
                    y = 1 - 2 * (i+.5) / 240
                    r = math.sqrt(1-y*y)
                    angle = i*2.399963
                    points.append((187*r*math.cos(angle),187*y,187*r*math.sin(angle)))
            if self._low and self._kind != 'cosmic':
                points = points[::2]
            for index, (x, y, z) in enumerate(points):
                size = 1.6 if index % 13 else 3.0
                seed = index * .618034 % 1
                for u, v in ((-1,-1),(1,-1),(1,1),(-1,-1),(1,1),(-1,1)):
                    if self._kind == 'cosmic':
                        data.extend((x,y,z,u,v,seed,1.3+seed*1.6))
                    else:
                        data.extend((x+u*size,y+v*size,z,u,v,seed,size))
        elif self._kind == 'globe':
            # Latitudes casi polares; el contorno transparente define la esfera.
            for ring, latitude in enumerate((-.92, -.78, .78, .92)):
                previous = None
                for step in range(181):
                    angle = step / 180 * math.tau
                    r = 187 * math.sqrt(1 - latitude * latitude)
                    point = (r * math.cos(angle), latitude * 187, r * math.sin(angle))
                    if previous:
                        emit(previous, (step-1)/180, ring*.21)
                        emit(point, step/180, ring*.21)
                    previous = point
        elif self._kind == 'circuits':
            for side in (-1, 1):
                for lane in range(9):
                    y = (lane - 4) * 12
                    # Desvíos menores que media separación: no se cruzan carriles.
                    skew = (lane % 3 - 1) * (4 if side < 0 else 3)
                    points = [(side*x, yy, -30) for x, yy in
                              ((470,y),(350,y),(334,y+skew),(260,y+skew),
                               (242,y),(198,y),(181,y+skew*.5))]
                    distance = 0.0
                    for a, b in zip(points, points[1:]):
                        emit(a, distance/290, lane*.123+side*.15)
                        distance += math.dist(a, b)
                        emit(b, distance/290, lane*.123+side*.15)
        else:
            raise ValueError(f'Tipo de geometría desconocido: {self._kind}')
        self.clear()
        self.setVertexData(data.tobytes())
        self.setStride(28 if triangles else 20)
        # Incluye amplitud máxima del shader cósmico para evitar recortes de culling.
        self.setBounds(QVector3D(-480,-310,-370), QVector3D(480,310,370))
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles if triangles else QQuick3DGeometry.PrimitiveType.Lines)
        sem, typ = QQuick3DGeometry.Attribute.Semantic, QQuick3DGeometry.Attribute.ComponentType
        self.addAttribute(sem.PositionSemantic, 0, typ.F32Type)
        self.addAttribute(sem.TexCoord0Semantic, 12, typ.F32Type)
        if triangles:
            self.addAttribute(sem.TexCoord1Semantic, 20, typ.F32Type)
        self.update()
