"""Ejecuta una copia completa fuera del proyecto, sin rutas de importación heredadas."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()
            and not {'previews', '__pycache__'}.intersection(p.relative_to(root).parts)}


def main():
    before = hashes(ROOT)
    output = ROOT/'previews'
    output.mkdir(exist_ok=True)
    report = {'result': 'FAIL', 'checks': []}
    try:
        with tempfile.TemporaryDirectory(prefix='EVA V53 autónoma ') as folder:
            base = Path(folder).resolve()
            assert base.parent == Path(tempfile.gettempdir()).resolve()
            clone = base/'Demo independiente'
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns('previews', '__pycache__', '.venv'))
            assert hashes(clone) == before
            env = os.environ.copy()
            for name in ('PYTHONPATH', 'QML_IMPORT_PATH', 'QML2_IMPORT_PATH'):
                env.pop(name, None)
            env['QML_DISABLE_DISK_CACHE'] = '1'
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            commands = [
                [sys.executable, '-B', str(clone/'run_demo.py'), '--low', '--state', 'HABLANDO',
                 '--capture', str(clone/'previews/portable-launch.png'), '--seconds', '3'],
                [sys.executable, '-B', str(clone/'tools/verify_matrix.py')],
            ]
            for command in commands:
                result = subprocess.run(command, cwd=base, env=env, capture_output=True,
                                        text=True, encoding='utf-8', errors='replace', timeout=180)
                assert result.returncode == 0, result.stdout + result.stderr
                assert not result.stderr.strip(), result.stderr
            matrix = json.loads((clone/'previews/matrix-validation.json').read_text(encoding='utf-8'))
            assert matrix['result'] == 'PASS'
            assert hashes(ROOT) == before, 'Se modificó el origen durante la prueba'
            assert hashes(clone) == before, 'La ejecución modificó archivos del paquete'
            shutil.copy2(clone/'previews/portable-launch.png', output/'portable-launch.png')
            report.update(result='PASS', files=len(before), matrix=matrix,
                          checks=['Lanzador público en HABLANDO y calidad reducida',
                                  'Copia sin caché QML ni rutas del proyecto: estados, máscara, zoom y cierre',
                                  'GLB, shaders compilados, atlas SVG y QML incluidos',
                                  'Archivos de origen y copia conservados por SHA-256'])
    except Exception as exc:
        report['error'] = str(exc)
    (output/'portability.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
