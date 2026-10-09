"""Componentes visuales y animaciones de SIGA."""

from pathlib import Path

from PySide6.QtCore import Property, QEasingCurve, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEAL = "#147d70"
MUTED = "#69777b"
STATUS_COLORS = {
    "APROBADO": ("#e8f5ed", "#267647"),
    "REPROBADO": ("#fbecee", "#a23f52"),
    "PENDIENTE": ("#fff6df", "#916d22"),
}


def icon(name, color="#36474b", size=20):
    path = ASSETS / "icons" / f"{name}.svg"
    if not path.exists():
        return QIcon()
    source = path.read_bytes().replace(b"currentColor", color.encode())
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(source).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def label(text, role="", wrap=False):
    widget = QLabel(text)
    widget.setWordWrap(wrap)
    if role:
        widget.setObjectName(role)
    return widget


class ActionButton(QPushButton):
    def __init__(self, text, symbol=None, primary=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setObjectName("primary" if primary else "action")
        if symbol:
            self.setIcon(icon(symbol, "#ffffff" if primary else "#36474b"))
        self.setIconSize(QSize(18, 18))
        self.setToolTip(text)


class NavButton(QPushButton):
    def __init__(self, text, symbol):
        super().__init__(text)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setIcon(icon(symbol, "#b8c9cc"))
        self.setIconSize(QSize(20, 20))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(text)


class Stat(QFrame):
    def __init__(self, title, symbol, color):
        super().__init__()
        self.setObjectName("stat")
        self.color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 17, 20, 17)
        heading = QHBoxLayout()
        heading.addWidget(label(title, "muted"))
        picture = QLabel()
        picture.setPixmap(icon(symbol, color).pixmap(22, 22))
        heading.addStretch()
        heading.addWidget(picture)
        layout.addLayout(heading)
        self.value = label("0", "statValue")
        layout.addWidget(self.value)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(650)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(lambda x: self.value.setText(str(round(x))))

    def set_value(self, value, animated=True):
        self.animation.stop()
        if animated:
            self.animation.setStartValue(float(self.value.text()))
            self.animation.setEndValue(float(value))
            self.animation.start()
        else:
            self.value.setText(str(value))


class ResultRing(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(180, 180)
        self.setMaximumHeight(210)
        self.counts = [0, 0, 0]
        self._progress = 1.0
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(850)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.set_progress)

    def set_progress(self, value):
        self._progress = float(value)
        self.update()

    progress = Property(float, lambda self: self._progress, set_progress)

    def set_counts(self, counts, animated=True):
        self.counts = counts
        self.animation.stop()
        if animated:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.set_progress(1.0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 40
        x, y = (self.width() - side) // 2, (self.height() - side) // 2
        painter.setPen(QPen(QColor("#edf1f2"), 15))
        painter.drawEllipse(x, y, side, side)
        total = sum(self.counts)
        start = 90 * 16
        for count, color in zip(self.counts, ["#32815a", "#b5586a", "#cfad52"]):
            if not count or not total:
                continue
            span = int(360 * 16 * count / total * self._progress)
            painter.setPen(QPen(QColor(color), 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            painter.drawArc(x, y, side, side, start, -span)
            start -= span
        painter.setPen(QColor("#25353b"))
        painter.setFont(QFont("Source Sans 3", 24, QFont.Weight.DemiBold))
        painter.drawText(
            self.rect().adjusted(0, -12, 0, -12),
            Qt.AlignmentFlag.AlignCenter,
            str(total),
        )
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Source Sans 3", 9))
        painter.drawText(
            self.rect().adjusted(0, 40, 0, 40),
            Qt.AlignmentFlag.AlignCenter,
            "inscripciones",
        )


class DataTable(QTableWidget):
    def __init__(self, headers):
        super().__init__(0, len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(48)
        self.horizontalHeader().setMinimumHeight(42)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWordWrap(False)
        self.setObjectName("dataTable")

    def fill(self, rows, columns, identifier="id"):
        self.setSortingEnabled(False)
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col, key in enumerate(columns):
                value = key(row) if callable(key) else row.get(key, "")
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                item.setData(Qt.ItemDataRole.UserRole, row.get(identifier))
                if col == 0:
                    item.setForeground(QColor("#147d70"))
                    item.setFont(QFont("Source Sans 3", 10, QFont.Weight.DemiBold))
                if str(value) in STATUS_COLORS:
                    background, color = STATUS_COLORS[str(value)]
                    item.setForeground(QColor(color))
                    item.setBackground(QColor(background))
                self.setItem(row_index, col, item)
        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)

    def selected_id(self):
        row = self.currentRow()
        item = self.item(row, 0) if row >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None


class FormDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(510)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(26, 24, 26, 24)
        self.layout.setSpacing(16)
        self.layout.addWidget(label(title, "dialogTitle"))
        self.error = label("", "error", True)
        self.error.hide()
        self.layout.addWidget(self.error)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primary")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.buttons.rejected.connect(self.reject)

    def finish_layout(self, save):
        self.layout.addWidget(self.buttons)
        self.buttons.accepted.connect(save)

    def show_error(self, message):
        self.error.setText(str(message))
        self.error.show()
