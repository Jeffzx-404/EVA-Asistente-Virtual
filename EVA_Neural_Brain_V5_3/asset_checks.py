"""Validación visual, funcional y de rendimiento en un único bucle Qt nativo."""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import struct
import sys
import time
import traceback

from PySide6.QtCore import QObject, QPointF, Qt, QTimer, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QSurfaceFormat, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick3D import QQuick3D
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
import geometry

ROOT = Path(__file__).resolve().parent


def validate_assets():
    manifest = json.loads((ROOT/'assets/manifest.json').read_text())
    for quality in ('high', 'low'):
        path = ROOT / f'assets/brain_{quality}.glb'
        raw = path.read_bytes()
        assert struct.unpack_from('<III', raw) == (0x46546C67, 2, len(raw))
        assert hashlib.sha256(raw).hexdigest() == manifest[quality]['sha256']
        vertices, indices, low, high = geometry.read_surface(quality)
        count = len(vertices)//24
        assert len(indices)//12 == manifest[quality]['triangles']
        assert count == manifest[quality]['vertices']
        assert all(0 <= index[0] < count for index in struct.iter_unpack('<I', indices))
        assert all(math.isfinite(value[0]) for value in struct.iter_unpack('<f', vertices))
        assert all(a < b for a, b in zip(low, high))
    assert manifest['low']['triangles'] < manifest['high']['triangles']*.6
    assert all(len(path) >= 12 for path in geometry.network()['paths'])
    for source in ROOT.rglob('*.py'):
        ast.parse(source.read_text(encoding='utf-8'))
    return manifest


def memory_mib():
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes
    class Memory(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
            'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    memory = Memory()
    memory.cb = ctypes.sizeof(memory)
    kernel = ctypes.WinDLL('kernel32')
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi')
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
    if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(memory), memory.cb):
        return round(memory.WorkingSetSize/1024**2, 1)
    return None
