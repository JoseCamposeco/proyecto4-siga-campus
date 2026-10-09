from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from .database import ValidationError
from .widgets import ActionButton, DataTable, FormDialog, icon, label


def input_text(value="", placeholder=""):
    field = QLineEdit(str(value))
    field.setPlaceholderText(placeholder)
    field.setMaxLength(180)
    return field


def combo(items, selected=None):
    widget = QComboBox()
    widget.setMinimumWidth(170)
    for text, value in items:
        widget.addItem(text, value)
    if selected is not None:
        index = widget.findData(selected)
        if index >= 0:
            widget.setCurrentIndex(index)
    return widget


def cover_fields(form, cover):
    fields = {}
    for key, title in [
        ("university", "Universidad"),
        ("career", "Carrera"),
        ("subject", "Curso"),
        ("teacher", "Docente"),
        ("team", "Equipo"),
    ]:
        fields[key] = input_text(cover[key])
        form.addRow(title, fields[key])
    members = QTextEdit()
    members.setPlainText(cover["members"])
    members.setMinimumHeight(125)
    fields["members"] = members
    form.addRow("Integrantes y carnés", members)
    return fields


def read_cover(fields):
    return {
        key: value.toPlainText() if isinstance(value, QTextEdit) else value.text()
        for key, value in fields.items()
    }


class CoverDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("SIGA Campus | Proyecto 4 - Algoritmos")
        self.setWindowIcon(icon("graduation-cap", "#147d70", 32))
        self.resize(890, 660)
        self.setMinimumSize(790, 620)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(245)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(30, 36, 30, 30)
        emblem = label("")
        emblem.setPixmap(icon("graduation-cap", "#9bc9bb", 68).pixmap(68, 68))
        side_layout.addWidget(emblem)
        side_layout.addSpacing(20)
        side_layout.addWidget(label("SIGA\nCampus", "brand"))
        side_layout.addSpacing(12)
        side_layout.addWidget(label("GESTIÓN ACADÉMICA\nUNIVERSITARIA", "brandSub", True))
        side_layout.addStretch()
        side_layout.addWidget(label("PROYECTO 04", "sidebarCaption"))
        side_layout.addSpacing(10)
        side_layout.addWidget(label("Python · SQLite\nVersión 1.0.0", "sidebarFoot"))
        outer.addWidget(side)
        content = QVBoxLayout()
        content.setContentsMargins(35, 28, 35, 26)
        content.setSpacing(14)
        outer.addLayout(content, 1)
        content.addWidget(label("PROYECTO FINAL · ALGORITMOS", "muted"))
        content.addWidget(label("Sistema de Gestión\nAcadémica Universitaria", "pageTitle"))
        self.cover_area = QVBoxLayout()
        content.addLayout(self.cover_area)
        self.refresh()
        content.addStretch()
        actions = QHBoxLayout()
        edit = ActionButton("Editar carátula", "pencil")
        edit.clicked.connect(self.edit_cover)
        self.enter = ActionButton("Entrar al sistema", "arrow-right", True)
        self.enter.setDefault(True)
        self.enter.clicked.connect(self.accept)
        actions.addWidget(edit)
        actions.addStretch()
        actions.addWidget(self.enter)
        content.addLayout(actions)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.reveal = QPropertyAnimation(self.effect, b"opacity", self)
        self.reveal.setDuration(550)
        self.reveal.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        if self.store.settings()["animations"]:
            self.reveal.setStartValue(0.0)
            self.reveal.setEndValue(1.0)
            self.reveal.start()
        else:
            self.effect.setOpacity(1.0)

    def refresh(self):
        while self.cover_area.count():
            item = self.cover_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cover = self.store.settings()["cover"]
        self.cover_area.addWidget(label(cover["university"], "sectionTitle", True))
        self.cover_area.addWidget(label(cover["career"], "muted", True))
        self.cover_area.addSpacing(5)
        self.cover_area.addWidget(label("INTEGRANTES", "muted"))
        for member in cover["members"].splitlines():
            self.cover_area.addWidget(label(member, wrap=True))
        self.cover_area.addSpacing(8)
        self.cover_area.addWidget(label("DOCENTE", "muted"))
        self.cover_area.addWidget(label(cover["teacher"], wrap=True))
        self.cover_area.addWidget(label(f"{cover['subject']} · {cover['team']}", "muted", True))

    def edit_cover(self):
        dialog = FormDialog("Datos de la carátula", self)
        dialog.resize(610, 540)
        form = QFormLayout()
        fields = cover_fields(form, self.store.settings()["cover"])
        dialog.layout.addLayout(form)

        def save():
            settings = self.store.settings()
            try:
                self.store.save_settings(
                    settings["passing"],
                    settings["cycle"],
                    settings["animations"],
                    read_cover(fields),
                )
                dialog.accept()
                self.refresh()
            except ValidationError as exc:
                dialog.show_error(exc)

        dialog.finish_layout(save)
        dialog.exec()


class PersonDialog(FormDialog):
    def __init__(self, store, kind, parent, identifier=None):
        super().__init__(
            ("Editar " if identifier else "Registrar ")
            + ("estudiante" if kind == "students" else "profesor"),
            parent,
        )
        record = store.require(kind, identifier) if identifier else {}
        form = QFormLayout()
        form.setSpacing(13)
        fields = {}
        extra = "career" if kind == "students" else "specialty"
        for key, title in [
            ("code", "Carné" if kind == "students" else "Código"),
            ("name", "Nombre completo"),
            ("email", "Correo electrónico"),
            (extra, "Carrera" if kind == "students" else "Especialidad"),
        ]:
            fields[key] = input_text(record.get(key, ""))
            fields[key].setObjectName(key)
            form.addRow(title, fields[key])
        self.layout.addLayout(form)

        def save():
            try:
                store.save_person(
                    kind,
                    fields["code"].text(),
                    fields["name"].text(),
                    fields["email"].text(),
                    fields[extra].text(),
                    identifier,
                )
                self.accept()
            except ValidationError as exc:
                self.show_error(exc)

        self.finish_layout(save)
        fields["code"].setFocus()


class CourseDialog(FormDialog):
    def __init__(self, store, parent, identifier=None):
        super().__init__("Editar curso" if identifier else "Registrar curso", parent)
        record = store.require("courses", identifier) if identifier else {}
        form = QFormLayout()
        form.setSpacing(13)
        code = input_text(record.get("code", ""))
        name = input_text(record.get("name", ""))
        cycle = input_text(record.get("cycle", store.settings()["cycle"]))
        credits = QSpinBox()
        credits.setRange(1, 30)
        credits.setValue(record.get("credits", 5))
        capacity = QSpinBox()
        capacity.setRange(1, 1000)
        capacity.setValue(record.get("capacity", 40))
        professor = combo(
            [(p["name"], p["id"]) for p in store.people("teachers")],
            record.get("teacher_id"),
        )
        for title, widget in [
            ("Código", code),
            ("Nombre del curso", name),
            ("Ciclo académico", cycle),
            ("Profesor responsable", professor),
            ("Créditos", credits),
            ("Cupo máximo", capacity),
        ]:
            form.addRow(title, widget)
        self.layout.addLayout(form)

        def save():
            try:
                store.save_course(
                    code.text(),
                    name.text(),
                    credits.value(),
                    cycle.text(),
                    professor.currentData(),
                    capacity.value(),
                    identifier,
                )
                self.accept()
            except ValidationError as exc:
                self.show_error(exc)

        self.finish_layout(save)


class PlanDialog(FormDialog):
    def __init__(self, store, course_id, parent):
        super().__init__("Plan de evaluación", parent)
        self.resize(580, 480)
        self.table = DataTable(["Evaluación", "Ponderación (%)"])
        from PySide6.QtWidgets import QAbstractItemView

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.fill(
            store.evaluations(course_id),
            ["name", lambda row: f"{row['weight'] / 100:g}"],
        )
        self.layout.addWidget(self.table)
        toolbar = QHBoxLayout()
        add = ActionButton("Agregar", "plus")
        remove = ActionButton("Quitar")
        total = label("Total: 100 %", "muted")

        def update_total():
            try:
                value = sum(
                    float(self.table.item(r, 1).text().replace(",", "."))
                    for r in range(self.table.rowCount())
                    if self.table.item(r, 1)
                )
                total.setText(f"Total: {value:g} %")
            except ValueError:
                total.setText("Total: pendiente")

        def add_row():
            index = self.table.rowCount()
            if index >= 12:
                self.show_error("El máximo es 12 evaluaciones.")
                return
            self.table.insertRow(index)
            self.table.setItem(index, 0, QTableWidgetItem("Nueva evaluación"))
            self.table.setItem(index, 1, QTableWidgetItem("0"))

        def remove_row():
            self.table.removeRow(self.table.currentRow())
            update_total()

        add.clicked.connect(add_row)
        remove.clicked.connect(remove_row)
        self.table.itemChanged.connect(update_total)
        toolbar.addWidget(add)
        toolbar.addWidget(remove)
        toolbar.addStretch()
        toolbar.addWidget(total)
        self.layout.addLayout(toolbar)

        def save():
            entries = [
                (
                    self.table.item(r, 0).text() if self.table.item(r, 0) else "",
                    self.table.item(r, 1).text() if self.table.item(r, 1) else "",
                )
                for r in range(self.table.rowCount())
            ]
            try:
                store.set_evaluation_plan(course_id, entries)
                self.accept()
            except ValidationError as exc:
                self.show_error(exc)

        self.finish_layout(save)
