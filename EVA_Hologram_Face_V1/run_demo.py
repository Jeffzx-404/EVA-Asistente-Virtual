"""EVA Hologram Face V1: maqueta funcional independiente, sin backend ni audio."""
import argparse
from pathlib import Path
import sys
from PySide6.QtCore import QObject, Slot, QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

ROOT = Path(__file__).resolve().parent


class DemoFiles(QObject):
    @Slot(QUrl, str, result=bool)
    def saveText(self, url, text):
        if not url.isLocalFile():
            return False
        try:
            Path(url.toLocalFile()).write_text(text, encoding='utf-8')
            return True
        except (OSError, ValueError):
            return False


def center_window(window, width=1338, height=753):
    """Fit the initial client area to its screen, including native frame margins."""
    area = window.screen().availableGeometry()
    margins = window.frameMargins()
    window.resize(
        max(window.minimumWidth(), min(width, area.width()-margins.left()-margins.right())),
        max(window.minimumHeight(), min(height, area.height()-margins.top()-margins.bottom())),
    )
    frame = window.frameGeometry()
    window.setFramePosition(area.center()-(frame.center()-frame.topLeft()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--seconds', type=float, default=3)
    parser.add_argument('--width', type=int, default=1338)
    parser.add_argument('--height', type=int, default=753)
    parser.add_argument('--maximized', action='store_true', help='Abrir maximizada')
    parser.add_argument('--reduced-motion', action='store_true', help='Desactivar microanimaciones de controles')
    args = parser.parse_args()
    app = QGuiApplication(sys.argv[:1])
    app.setFont(QFont('Arial'))
    app.setApplicationName('EVA Hologram Face V1')
    app.setOrganizationName('EVA Demo')
    QQuickStyle.setStyle('Basic')
    engine = QQmlApplicationEngine()
    files = DemoFiles(app)
    engine.rootContext().setContextProperty('demoFiles', files)
    engine.load(QUrl.fromLocalFile(str(ROOT/'qml/Main.qml')))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    window.setProperty('reducedMotion', args.reduced_motion)
    center_window(window, args.width, args.height)
    if args.maximized:
        window.showMaximized()
    timer = QTimer(app)
    timer.setSingleShot(True)
    errors = []
    if args.capture:
        def capture():
            args.capture.parent.mkdir(parents=True,exist_ok=True)
            if not window.grabWindow().save(str(args.capture)):
                errors.append('captura')
            window.close()
        timer.timeout.connect(capture)
        timer.start(max(1000,int(args.seconds*1000)))
    app.aboutToQuit.connect(timer.stop)
    code = app.exec()
    del engine
    return 1 if errors else code


if __name__ == '__main__':
    raise SystemExit(main())
