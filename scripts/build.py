"""Compilar el ejecutable Windows desde la raiz del proyecto."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    if os.name != "nt":
        raise SystemExit("El ejecutable .exe debe compilarse en Windows.")
    root = Path(__file__).resolve().parent.parent
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PIL import Image
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    app = QGuiApplication.instance() or QGuiApplication([])
    target = root / "build"
    target.mkdir(exist_ok=True)
    pixmap = QPixmap(256, 256)
    pixmap.fill(QColor("#147d70"))
    painter = QPainter(pixmap)
    source = (
        (root / "assets/icons/graduation-cap.svg").read_bytes().replace(b"currentColor", b"#ffffff")
    )
    QSvgRenderer(source).render(painter, QRectF(38, 38, 180, 180))
    painter.end()
    pixmap.save(str(target / "icon.png"))
    with Image.open(target / "icon.png") as image:
        image.save(
            target / "icon.ico",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "SIGA-Campus",
        "--icon",
        str(target / "icon.ico"),
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(target / "pyinstaller"),
        "--specpath",
        str(target),
        "--add-data",
        str(root / "assets") + ";assets",
        "--add-data",
        str(root / "THIRD_PARTY_NOTICES.md") + ";.",
        "--exclude-module",
        "PySide6.QtWebEngineCore",
        "--exclude-module",
        "PySide6.QtWebEngineWidgets",
        "--exclude-module",
        "PySide6.QtPdf",
        "--exclude-module",
        "pytest",
        str(root / "main.py"),
    ]
    # Select DLLs from Python, Qt and Windows, independent of unrelated tools on PATH.
    from PySide6 import __file__ as qt_package

    environment = dict(os.environ)
    windows = Path(os.environ["SystemRoot"])
    environment["PATH"] = os.pathsep.join(
        str(path)
        for path in [
            Path(sys.executable).parent,
            Path(sys.base_prefix),
            Path(sys.base_prefix) / "DLLs",
            Path(qt_package).parent,
            windows / "System32",
            windows,
        ]
    )
    subprocess.run(command, cwd=root, env=environment, check=True)
    print(root / "dist" / "SIGA-Campus.exe")
    app.quit()


if __name__ == "__main__":
    main()
