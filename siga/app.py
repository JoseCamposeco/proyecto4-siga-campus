from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .dialogs import CoverDialog
from .pages import (
    CoursesPage,
    DashboardPage,
    EnrollmentPage,
    GradesPage,
    HistoryPage,
    PeoplePage,
    SettingsPage,
)
from .widgets import ActionButton, NavButton, icon, label


class MainWindow(QMainWindow):
    def __init__(self, store, data_path):
        super().__init__()
        self.store = store
        self.data_path = Path(data_path)
        self.setWindowTitle("SIGA Campus | Gestión Académica Universitaria")
        self.setWindowIcon(icon("graduation-cap", "#147d70", 32))
        self.resize(1320, 850)
        self.setMinimumSize(1100, 700)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(208)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(17, 27, 17, 22)
        emblem = label("")
        emblem.setPixmap(icon("graduation-cap", "#9bc9bb", 42).pixmap(42, 42))
        side.addWidget(emblem)
        side.addSpacing(9)
        side.addWidget(label("SIGA", "brand"))
        side.addWidget(label("CAMPUS · GESTIÓN ACADÉMICA", "brandSub"))
        side.addSpacing(28)
        side.addWidget(label("ADMINISTRACIÓN", "sidebarCaption"))
        side.addSpacing(10)
        self.nav = {}
        nav_items = [
            ("dashboard", "Resumen", "layout-dashboard"),
            ("students", "Estudiantes", "users"),
            ("teachers", "Profesores", "user-round"),
            ("courses", "Cursos", "book-open"),
            ("enrollments", "Inscripciones", "clipboard-list"),
            ("grades", "Calificaciones", "chart-no-axes-combined"),
            ("history", "Historial académico", "file-text"),
        ]
        for key, text, symbol in nav_items:
            button = NavButton(text, symbol)
            button.clicked.connect(lambda checked=False, key=key: self.navigate(key))
            side.addWidget(button)
            self.nav[key] = button
        side.addStretch()
        settings = NavButton("Configuración", "settings")
        settings.clicked.connect(lambda: self.navigate("settings"))
        self.nav["settings"] = settings
        side.addWidget(settings)
        side.addSpacing(18)
        side.addWidget(label("PROYECTO 4 · ALGORITMOS", "sidebarCaption"))
        side.addWidget(label("Versión 1.0.0\nDatos guardados localmente", "sidebarFoot"))
        self.nav_marker = QFrame(sidebar)
        self.nav_marker.setFixedSize(3, 28)
        self.nav_marker.setStyleSheet("background: #a4d1c2; border-radius: 1px;")
        self.nav_marker.hide()
        self.marker_animation = QPropertyAnimation(self.nav_marker, b"pos", self)
        self.marker_animation.setDuration(320)
        self.marker_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        layout.addWidget(sidebar)
        workspace = QVBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(67)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(28, 0, 28, 0)
        self.breadcrumb = label("Campus / Resumen", "breadcrumb")
        top.addWidget(self.breadcrumb)
        top.addStretch()
        self.cycle = label("", "cycleChip")
        top.addWidget(self.cycle)
        cover = ActionButton("Carátula", "graduation-cap")
        cover.clicked.connect(self.show_cover)
        top.addWidget(cover)
        workspace.addWidget(topbar)
        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(self),
            "students": PeoplePage(self, "students"),
            "teachers": PeoplePage(self, "teachers"),
            "courses": CoursesPage(self),
            "enrollments": EnrollmentPage(self),
            "grades": GradesPage(self),
            "history": HistoryPage(self),
            "settings": SettingsPage(self),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        workspace.addWidget(self.stack, 1)
        self.toast = label("", "toast", True)
        self.toast.hide()
        workspace.addWidget(self.toast)
        layout.addLayout(workspace, 1)
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast.hide)
        self.current_key = "dashboard"
        self.effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(240)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.navigate("dashboard", initial=True)

    def navigate(self, key, initial=False):
        if not initial and not self.can_leave():
            self.nav[self.current_key].setChecked(True)
            self.nav[key].setChecked(key == self.current_key)
            return False
        self.current_key = key
        self.stack.setCurrentWidget(self.pages[key])
        for nav_key, button in self.nav.items():
            button.setChecked(nav_key == key)
        self.breadcrumb.setText(f"Campus / {self.nav[key].text()}")
        self.refresh()
        self.move_marker()
        self.animation.stop()
        if self.store.settings()["animations"]:
            self.animation.setStartValue(0.35)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.effect.setOpacity(1.0)
        return True

    def move_marker(self):
        if not self.isVisible():
            return
        button = self.nav[self.current_key]
        destination = QPoint(8, button.y() + (button.height() - 28) // 2)
        self.marker_animation.stop()
        if self.store.settings()["animations"] and self.nav_marker.isVisible():
            self.marker_animation.setStartValue(self.nav_marker.pos())
            self.marker_animation.setEndValue(destination)
            self.marker_animation.start()
        else:
            self.nav_marker.move(destination)
        self.nav_marker.show()

    def showEvent(self, event):
        super().showEvent(event)
        self.move_marker()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "nav_marker"):
            QTimer.singleShot(0, self.move_marker)

    def can_leave(self):
        if self.current_key == "grades":
            return self.pages["grades"].can_leave()
        return True

    def refresh(self):
        settings = self.store.settings()
        self.cycle.setText(f"Ciclo {settings['cycle']}")
        self.pages[self.current_key].refresh()

    def notify(self, text, error=False):
        self.toast.setText(text)
        self.toast.setStyleSheet(
            "background: #a23f52; color: white; padding: 12px 20px; border-radius: 6px;"
            if error
            else ""
        )
        self.toast.show()
        self.toast_timer.start(7000 if error else 4000)

    def open_course(self, identifier, target):
        if identifier and self.navigate(target):
            widget = self.pages[target].course
            widget.setCurrentIndex(widget.findData(identifier))

    def open_student(self, identifier):
        if self.navigate("history"):
            widget = self.pages["history"].student
            widget.setCurrentIndex(widget.findData(identifier))

    def show_cover(self):
        CoverDialog(self.store, self).exec()
        self.refresh()

    def closeEvent(self, event):
        if self.can_leave():
            event.accept()
        else:
            event.ignore()
