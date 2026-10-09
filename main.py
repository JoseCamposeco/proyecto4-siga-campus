"""Entrada de escritorio. Ejecutar: python main.py"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="SIGA Campus - Proyecto 4")
    parser.add_argument("--data-dir", type=Path, help="Carpeta alternativa para los datos")
    parser.add_argument(
        "--smoke-test",
        type=Path,
        help="Autoverificación sin interacción; archivo JSON de resultado",
    )
    args = parser.parse_args()
    if args.smoke_test:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

    from siga.app import MainWindow
    from siga.database import AcademicStore
    from siga.dialogs import CoverDialog
    from siga.theme import configure_app

    app = QApplication(sys.argv[:1])
    app.setOrganizationName("Proyecto4")
    app.setApplicationName("SIGA Campus")
    configure_app(app)
    directory = args.data_dir or Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    directory.mkdir(parents=True, exist_ok=True)
    store = AcademicStore(directory / "siga.db")

    def handle_exception(exc_type, value, tb):
        message = "".join(traceback.format_exception(exc_type, value, tb))
        (directory / "errores.log").write_text(message, encoding="utf-8")
        QMessageBox.critical(
            None,
            "Error inesperado",
            f"No se pudo completar la operación. Detalle en:\n{directory / 'errores.log'}",
        )

    sys.excepthook = handle_exception
    try:
        if args.smoke_test:
            store.load_demo()
            window = MainWindow(store, directory / "siga.db")
            for key in window.pages:
                window.navigate(key)
                app.processEvents()
            cover = CoverDialog(store)
            result = {
                "ok": True,
                "pages": list(window.pages),
                "stats": store.dashboard(),
                "cover_members": store.settings()["cover"]["members"].splitlines(),
                "passing": store.settings()["passing"],
            }
            args.smoke_test.parent.mkdir(parents=True, exist_ok=True)
            args.smoke_test.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            cover.close()
            window.close()
            return 0
        if CoverDialog(store).exec() != QDialog.DialogCode.Accepted:
            return 0
        window = MainWindow(store, directory / "siga.db")
        window.show()
        return app.exec()
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
