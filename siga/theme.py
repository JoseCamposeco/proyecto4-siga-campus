from PySide6.QtGui import QFont, QFontDatabase

from .widgets import ASSETS


def configure_app(app):
    QFontDatabase.addApplicationFont(str(ASSETS / "fonts" / "SourceSans3.ttf"))
    app.setFont(QFont("Source Sans 3", 10))
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE.replace("assets/icons/", ASSETS.as_posix() + "/icons/"))


STYLE = """
* { font-family: 'Source Sans 3'; font-size: 14px; }
QWidget { color: #293b40; background: #f6f8f9; }
QMainWindow, QDialog { background: #f6f8f9; }
QLabel { background: transparent; }
QFrame#sidebar { background: #202a2e; border: none; }
QLabel#brand { color: #ffffff; font-size: 28px; font-weight: 700; }
QLabel#brandSub { color: #b7c9cc; font-size: 11px; }
QLabel#sidebarCaption { color: #91a5aa; font-size: 10px; font-weight: 600; }
QLabel#sidebarFoot { color: #9cb0b5; font-size: 11px; }
QPushButton#nav { background: transparent; color: #bfd0d3; text-align: left;
 padding: 0 14px; border: 0; border-radius: 6px; }
QPushButton#nav:hover { background: #2d3c40; color: #ffffff; }
QPushButton#nav:checked { background: #176f63; color: #ffffff; font-weight: 600; }
QFrame#topbar { background: #ffffff; border-bottom: 1px solid #e1e7e9; }
QLabel#breadcrumb { color: #64757b; font-size: 12px; }
QLabel#cycleChip { background: #edf5f3; color: #286d62; padding: 7px 12px; border-radius: 4px; }
QLabel#pageTitle { font-size: 27px; font-weight: 600; color: #22343a; }
QLabel#subtitle, QLabel#muted { color: #708087; }
QLabel#sectionTitle { font-size: 16px; font-weight: 600; }
QLabel#dialogTitle { font-size: 21px; font-weight: 600; }
QLabel#error { background: #fbecee; color: #a13d50; padding: 12px; border-radius: 5px; }
QLabel#notice { background: #edf5f3; color: #2b7669; padding: 12px; border-radius: 5px; }
QLabel#toast { background: #233e37; color: white; padding: 12px 20px; border-radius: 6px; }
QFrame#stat { background: #ffffff; border: 1px solid #e2e8ea; border-radius: 6px; }
QLabel#statValue { font-size: 32px; font-weight: 600; color: #263c40; }
QPushButton { background: #ffffff; border: 1px solid #d8e1e4; border-radius: 5px; padding: 9px 13px; }
QPushButton:hover { background: #edf3f3; border-color: #96b3ae; }
QPushButton:pressed { background: #dfecea; }
QPushButton:focus { border: 2px solid #147d70; }
QPushButton#primary { background: #147d70; color: white; border: 1px solid #147d70; font-weight: 600; }
QPushButton#primary:hover { background: #116b61; border-color: #116b61; }
QPushButton#primary:pressed { background: #0f5d55; }
QPushButton:disabled { background: #edf0f1; color: #9aa8ac; border-color: #e3e8ea; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit { background: #ffffff; border: 1px solid #d6e0e3;
 border-radius: 5px; padding: 9px 11px; min-height: 20px; selection-background-color: #147d70; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus { border: 1px solid #147d70; }
QComboBox::drop-down { border: 0; width: 26px; }
QComboBox::down-arrow { image: url("assets/icons/chevron-down.svg"); width: 14px; height: 14px; }
QComboBox QAbstractItemView { background: white; color: #293b40; selection-background-color: #dcefe9; selection-color: #194f44; }
QTableWidget { background: #ffffff; alternate-background-color: #fafcfc; border: 1px solid #e2e8ea;
 border-radius: 5px; selection-background-color: #e5f2ee; selection-color: #223d35; }
QTableWidget::item { padding: 9px 12px; border-bottom: 1px solid #edf1f2; }
QTableWidget::item:selected { background: #e5f2ee; color: #234f43; }
QHeaderView::section { background: #f0f4f5; border: 0; border-bottom: 1px solid #e0e7e9;
 color: #61747b; padding: 11px 12px; font-weight: 600; font-size: 11px; }
QScrollBar:vertical { background: #f1f4f5; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #c6d2d6; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #f1f4f5; height: 9px; }
QScrollBar::handle:horizontal { background: #c6d2d6; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QProgressBar { background: #e6eeed; border: 0; border-radius: 3px; height: 7px; }
QProgressBar::chunk { background: #147d70; border-radius: 3px; }
QCheckBox { spacing: 10px; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #a5b8bb; border-radius: 3px; background: white; }
QCheckBox::indicator:checked { background: #147d70; border: 1px solid #147d70; }
QTabWidget::pane { border: 0; background: #f6f8f9; }
QTabBar::tab { background: transparent; color: #71838a; padding: 11px 20px; border-bottom: 2px solid #e1e8ea; }
QTabBar::tab:selected { color: #147d70; border-bottom: 2px solid #147d70; font-weight: 600; }
QToolTip { background: #25363b; color: white; border: 0; padding: 6px; }
QScrollArea { border: 0; }
"""
