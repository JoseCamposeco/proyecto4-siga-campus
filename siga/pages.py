from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QDoubleValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QStyledItemDelegate,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .database import ValidationError
from .dialogs import (
    CourseDialog,
    PersonDialog,
    PlanDialog,
    combo,
    cover_fields,
    input_text,
    read_cover,
)
from .widgets import ActionButton, DataTable, ResultRing, Stat, icon, label


class Page(QWidget):
    def __init__(self, window, title, subtitle):
        super().__init__()
        self.window = window
        self.store = window.store
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(28, 25, 28, 20)
        self.body.setSpacing(18)
        heading = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(5)
        text.addWidget(label(title, "pageTitle"))
        text.addWidget(label(subtitle, "subtitle"))
        heading.addLayout(text)
        heading.addStretch()
        self.heading_actions = heading
        self.body.addLayout(heading)

    def attempt(self, operation, message=None):
        try:
            result = operation()
            if message:
                self.window.notify(message)
            self.window.refresh()
            return result
        except (ValidationError, OSError) as exc:
            self.window.notify(str(exc), error=True)
            return None

    def export(self, course_id=None, student_id=None):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar resultados", "resultados_academicos.csv", "CSV (*.csv)"
        )
        if filename:
            self.attempt(
                lambda: self.store.export_results(filename, course_id, student_id),
                "Reporte exportado",
            )


class DashboardPage(Page):
    def __init__(self, window):
        super().__init__(
            window,
            "Resumen académico",
            "Control del ciclo y actividad de la universidad",
        )
        self.demo_button = ActionButton("Cargar demostración", "flask-conical")
        self.demo_button.clicked.connect(self.demo)
        self.heading_actions.addWidget(self.demo_button)
        add = ActionButton("Nueva inscripción", "plus", True)
        add.clicked.connect(lambda: window.navigate("enrollments"))
        self.heading_actions.addWidget(add)
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.stats = {}
        for key, title, symbol, color in [
            ("students", "Estudiantes", "users", "#147d70"),
            ("teachers", "Profesores", "user-round", "#7675a6"),
            ("courses", "Cursos", "book-open", "#aa7e2b"),
            ("enrollments", "Inscripciones", "clipboard-list", "#a45a72"),
        ]:
            self.stats[key] = Stat(title, symbol, color)
            stats.addWidget(self.stats[key])
        self.body.addLayout(stats)
        panels = QHBoxLayout()
        panels.setSpacing(26)
        left = QVBoxLayout()
        title = QHBoxLayout()
        title.addWidget(label("Oferta académica", "sectionTitle"))
        title.addStretch()
        view = ActionButton("Ver cursos", "arrow-right")
        view.clicked.connect(lambda: window.navigate("courses"))
        title.addWidget(view)
        left.addLayout(title)
        self.table = DataTable(["CÓDIGO", "CURSO", "INSCRITOS", "CICLO"])
        self.table.setMinimumHeight(200)
        self.table.cellDoubleClicked.connect(self.open_course)
        left.addWidget(self.table, 1)
        panels.addLayout(left, 3)
        right = QVBoxLayout()
        right.addWidget(label("Resultados académicos", "sectionTitle"))
        self.ring = ResultRing()
        right.addWidget(self.ring)
        self.result_labels = {}
        for key, text, color in [
            ("approved", "Aprobados", "#32815a"),
            ("failed", "Reprobados", "#b5586a"),
            ("pending", "Pendientes", "#ad8a36"),
        ]:
            widget = label(text)
            widget.setStyleSheet(f"color: {color}; padding: 3px 0;")
            self.result_labels[key] = widget
            right.addWidget(widget)
        right.addStretch()
        panels.addLayout(right, 1)
        self.body.addLayout(panels, 2)
        self.body.addWidget(label("Actividad reciente · UTC", "sectionTitle"))
        self.activity_table = DataTable(["OPERACIÓN", "DETALLE", "FECHA"])
        self.activity_table.setMinimumHeight(130)
        self.body.addWidget(self.activity_table, 1)

    def refresh(self):
        stats = self.store.dashboard()
        animated = self.store.settings()["animations"]
        for key, widget in self.stats.items():
            widget.set_value(stats[key], animated)
        self.demo_button.setVisible(stats["students"] == stats["teachers"] == stats["courses"] == 0)
        self.table.fill(
            self.store.courses()[:6],
            [
                "code",
                "name",
                lambda row: f"{row['enrolled']} / {row['capacity']}",
                "cycle",
            ],
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.ring.set_counts([stats["approved"], stats["failed"], stats["pending"]], animated)
        for key, widget in self.result_labels.items():
            widget.setText(
                f"{ {'approved': 'Aprobados', 'failed': 'Reprobados', 'pending': 'Pendientes'}[key] }     {stats[key]}"
            )
        self.activity_table.fill(self.store.activity(4), ["action", "detail", "created"])
        self.activity_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

    def demo(self):
        answer = QMessageBox.question(
            self,
            "Datos de demostración",
            "¿Cargar estudiantes, profesores y cursos ficticios para la presentación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.attempt(self.store.load_demo, "Demostración cargada")

    def open_course(self, row, col):
        identifier = self.table.selected_id()
        if identifier:
            self.window.open_course(identifier, "grades")


class PeoplePage(Page):
    def __init__(self, window, kind):
        self.kind = kind
        student = kind == "students"
        super().__init__(
            window,
            "Estudiantes" if student else "Profesores",
            "Directorio académico de la universidad",
        )
        new = ActionButton(
            "Registrar estudiante" if student else "Registrar profesor", "plus", True
        )
        new.clicked.connect(lambda: self.edit())
        self.heading_actions.addWidget(new)
        toolbar = QHBoxLayout()
        self.search = input_text(placeholder="Buscar por código, nombre o correo")
        self.search.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search, 1)
        edit = ActionButton("Editar", "pencil")
        edit.clicked.connect(self.edit_selected)
        toolbar.addWidget(edit)
        if student:
            history = ActionButton("Historial académico", "file-text")
            history.clicked.connect(self.history)
            toolbar.addWidget(history)
        self.body.addLayout(toolbar)
        self.table = DataTable(
            [
                "CARNÉ" if student else "CÓDIGO",
                "NOMBRE COMPLETO",
                "CORREO ELECTRÓNICO",
                "CARRERA" if student else "ESPECIALIDAD",
            ]
        )
        self.table.cellDoubleClicked.connect(lambda r, c: self.edit_selected())
        self.body.addWidget(self.table, 1)
        self.count = label("", "muted")
        self.body.addWidget(self.count)

    def refresh(self):
        rows = self.store.people(self.kind, self.search.text())
        self.table.fill(
            rows,
            [
                "code",
                "name",
                "email",
                "career" if self.kind == "students" else "specialty",
            ],
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.count.setText(f"{len(rows)} registros")

    def edit(self, identifier=None):
        if PersonDialog(self.store, self.kind, self, identifier).exec():
            self.window.refresh()
            self.window.notify("Registro guardado")

    def edit_selected(self):
        identifier = self.table.selected_id()
        if identifier:
            self.edit(identifier)
        else:
            self.window.notify("Selecciona un registro", True)

    def history(self):
        identifier = self.table.selected_id()
        if identifier:
            self.window.open_student(identifier)
        else:
            self.window.notify("Selecciona un estudiante", True)


class CoursesPage(Page):
    def __init__(self, window):
        super().__init__(window, "Cursos", "Oferta, profesores responsables y planes de evaluación")
        new = ActionButton("Registrar curso", "plus", True)
        new.clicked.connect(self.new_course)
        self.heading_actions.addWidget(new)
        tools = QHBoxLayout()
        self.search = input_text(placeholder="Buscar curso, profesor o ciclo")
        self.search.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self.refresh)
        tools.addWidget(self.search, 1)
        for text, symbol, callback in [
            ("Editar", "pencil", self.edit),
            ("Evaluaciones", "clipboard-list", self.plan),
            ("Inscritos", "users", self.roster),
            ("Cerrar", "lock-keyhole", self.close_course),
        ]:
            button = ActionButton(text, symbol)
            button.clicked.connect(callback)
            tools.addWidget(button)
        self.body.addLayout(tools)
        self.table = DataTable(
            ["CÓDIGO", "CURSO", "PROFESOR", "CICLO", "CRÉDITOS", "CUPO", "ESTADO"]
        )
        self.table.cellDoubleClicked.connect(lambda r, c: self.roster())
        self.body.addWidget(self.table, 1)
        self.count = label("", "muted")
        self.body.addWidget(self.count)

    def refresh(self):
        rows = self.store.courses(self.search.text())
        self.table.fill(
            rows,
            [
                "code",
                "name",
                "teacher",
                "cycle",
                "credits",
                lambda r: f"{r['enrolled']} / {r['capacity']}",
                lambda r: "Cerrado" if r["closed"] else "En curso",
            ],
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.count.setText(f"{len(rows)} cursos")

    def selected(self):
        identifier = self.table.selected_id()
        if identifier is None:
            self.window.notify("Selecciona un curso", True)
        return identifier

    def new_course(self):
        if not self.store.people("teachers"):
            self.window.notify("Registra un profesor antes de crear el curso", True)
            self.window.navigate("teachers")
            return
        if CourseDialog(self.store, self).exec():
            self.window.refresh()
            self.window.notify("Curso registrado")

    def edit(self):
        identifier = self.selected()
        if identifier and CourseDialog(self.store, self, identifier).exec():
            self.window.refresh()
            self.window.notify("Curso actualizado")

    def plan(self):
        identifier = self.selected()
        if identifier and PlanDialog(self.store, identifier, self).exec():
            self.window.refresh()
            self.window.notify("Plan de evaluación guardado")

    def roster(self):
        identifier = self.selected()
        if identifier:
            self.window.open_course(identifier, "enrollments")

    def close_course(self):
        identifier = self.selected()
        if (
            identifier
            and QMessageBox.question(
                self,
                "Cerrar curso",
                "¿Cerrar el curso y proteger sus inscripciones y plan de evaluación? Las notas completas pueden corregirse y quedarán auditadas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.attempt(lambda: self.store.close_course(identifier), "Curso cerrado")


def update_combo(widget, items):
    previous = widget.currentData()
    widget.blockSignals(True)
    widget.clear()
    for text, identifier in items:
        widget.addItem(text, identifier)
    index = widget.findData(previous)
    if index >= 0:
        widget.setCurrentIndex(index)
    widget.blockSignals(False)


class EnrollmentPage(Page):
    def __init__(self, window):
        super().__init__(window, "Inscripciones", "Estudiantes inscritos por curso y ciclo")
        export = ActionButton("Exportar", "download")
        export.clicked.connect(lambda: self.export(course_id=self.course.currentData()))
        self.heading_actions.addWidget(export)
        tools = QHBoxLayout()
        self.course = combo([])
        self.course.currentIndexChanged.connect(self.refresh_roster)
        self.student = combo([])
        self.student.setMinimumWidth(250)
        enroll = ActionButton("Inscribir estudiante", "plus", True)
        enroll.clicked.connect(self.enroll)
        tools.addWidget(label("Curso"))
        tools.addWidget(self.course, 1)
        tools.addWidget(self.student, 1)
        tools.addWidget(enroll)
        self.body.addLayout(tools)
        self.info = label("", "notice", True)
        self.body.addWidget(self.info)
        self.table = DataTable(["CARNÉ", "ESTUDIANTE", "EVALUACIONES", "NOTA", "RESULTADO"])
        self.table.cellDoubleClicked.connect(self.history)
        self.body.addWidget(self.table, 1)
        actions = QHBoxLayout()
        self.count = label("", "muted")
        actions.addWidget(self.count)
        actions.addStretch()
        grades = ActionButton("Calificaciones", "arrow-right")
        grades.clicked.connect(
            lambda: (
                window.open_course(self.course.currentData(), "grades")
                if self.course.currentData()
                else None
            )
        )
        actions.addWidget(grades)
        self.body.addLayout(actions)

    def refresh(self):
        update_combo(
            self.course,
            [(f"{c['code']} · {c['name']} · {c['cycle']}", c["id"]) for c in self.store.courses()],
        )
        update_combo(
            self.student,
            [(f"{s['code']} · {s['name']}", s["id"]) for s in self.store.people("students")],
        )
        self.refresh_roster()

    def refresh_roster(self):
        identifier = self.course.currentData()
        rows = self.store.results(course_id=identifier) if identifier else []
        self.table.fill(
            rows,
            [
                "student_code",
                "student",
                lambda r: f"{r['completed']} / {r['evaluations']}",
                lambda r: f"{r['final']:.2f}",
                "status",
            ],
            "student_id",
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if identifier:
            course = self.store.require("courses", identifier)
            teacher = self.store.require("teachers", course["teacher_id"])
            self.info.setText(
                f"Profesor: {teacher['name']}     ·     Cupo: {len(rows)} / {course['capacity']}     ·     {'Cerrado' if course['closed'] else 'En curso'}"
            )
        else:
            self.info.setText("Sin cursos registrados")
        self.count.setText(f"{len(rows)} estudiantes inscritos")

    def enroll(self):
        if not self.course.currentData() or not self.student.currentData():
            self.window.notify("Selecciona un curso y un estudiante", True)
            return
        self.attempt(
            lambda: self.store.enroll(self.student.currentData(), self.course.currentData()),
            "Inscripción registrada",
        )

    def history(self, row, col):
        identifier = self.table.selected_id()
        if identifier:
            self.window.open_student(identifier)


class GradeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(0.0, 100.0, 2, editor))
        return editor


class GradesPage(Page):
    def __init__(self, window):
        super().__init__(window, "Calificaciones", "Registro de evaluaciones y promedio ponderado")
        self.dirty = False
        self.current_id = None
        self.records = []
        self.evaluations = []
        self.loading = False
        self.save_button = ActionButton("Guardar notas", "save", True)
        self.save_button.clicked.connect(self.save)
        self.heading_actions.addWidget(self.save_button)
        tools = QHBoxLayout()
        self.course = combo([])
        self.course.currentIndexChanged.connect(self.switch_course)
        tools.addWidget(label("Curso"))
        tools.addWidget(self.course, 1)
        plan = ActionButton("Plan de evaluación", "clipboard-list")
        plan.clicked.connect(self.plan)
        export = ActionButton("Exportar", "download")
        export.clicked.connect(lambda: self.export(course_id=self.course.currentData()))
        tools.addWidget(plan)
        tools.addWidget(export)
        self.body.addLayout(tools)
        self.note = label("", "notice", True)
        self.body.addWidget(self.note)
        self.table = DataTable(["CARNÉ", "ESTUDIANTE", "NOTA", "RESULTADO"])
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.table.setItemDelegate(GradeDelegate(self.table))
        self.table.itemChanged.connect(self.mark_dirty)
        self.body.addWidget(self.table, 1)
        self.summary = label("", "muted")
        self.body.addWidget(self.summary)

    def can_leave(self):
        if not self.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "Hay calificaciones sin guardar. ¿Guardar antes de continuar?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if result == QMessageBox.StandardButton.Save:
            return self.save()
        if result == QMessageBox.StandardButton.Discard:
            self.dirty = False
            return True
        return False

    def refresh(self):
        if self.dirty:
            return
        update_combo(
            self.course,
            [(f"{c['code']} · {c['name']} · {c['cycle']}", c["id"]) for c in self.store.courses()],
        )
        self.current_id = self.course.currentData()
        self.load_table()

    def switch_course(self):
        new = self.course.currentData()
        if self.dirty and not self.can_leave():
            self.course.blockSignals(True)
            self.course.setCurrentIndex(self.course.findData(self.current_id))
            self.course.blockSignals(False)
            return
        self.current_id = new
        self.load_table()

    def load_table(self):
        self.loading = True
        identifier = self.current_id
        self.evaluations = self.store.evaluations(identifier) if identifier else []
        self.records = self.store.results(course_id=identifier) if identifier else []
        headers = (
            ["CARNÉ", "ESTUDIANTE"]
            + [f"{e['name'].upper()}\n{e['weight'] / 100:g} %" for e in self.evaluations]
            + ["NOTA", "RESULTADO"]
        )
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setMinimumHeight(58)
        self.table.setRowCount(len(self.records))
        for row_index, record in enumerate(self.records):
            values = (
                [record["student_code"], record["student"]]
                + [
                    f"{record['grades'][e['id']]:g}" if e["id"] in record["grades"] else ""
                    for e in self.evaluations
                ]
                + [f"{record['final']:.2f}", record["status"]]
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if 2 <= col < 2 + len(self.evaluations):
                    item.setBackground(QColor("#f1f8f5"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setToolTip(f"{self.evaluations[col - 2]['name']} · 0 a 100 puntos")
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if value == "APROBADO":
                    item.setForeground(QColor("#267647"))
                elif value == "REPROBADO":
                    item.setForeground(QColor("#a23f52"))
                elif value == "PENDIENTE":
                    item.setForeground(QColor("#916d22"))
                self.table.setItem(row_index, col, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.loading = False
        self.dirty = False
        self.save_button.setEnabled(False)
        settings = self.store.settings()
        self.note.setText(
            f"Escala: 0 a 100 puntos     ·     Aprobación: {settings['passing']:g}     ·     Ponderación: {sum(e['weight'] for e in self.evaluations) / 100:g} %"
        )
        total = len(self.records) * len(self.evaluations)
        completed = sum(r["completed"] for r in self.records)
        self.summary.setText(
            f"{len(self.records)} estudiantes     ·     {completed} / {total} calificaciones registradas"
        )

    def mark_dirty(self, item):
        if self.loading or not 2 <= item.column() < 2 + len(self.evaluations):
            return
        self.dirty = True
        self.save_button.setEnabled(True)
        self.summary.setText("Cambios sin guardar")

    def save(self):
        if not self.current_id:
            return True
        self.table.setCurrentCell(-1, -1)
        self.table.clearFocus()
        changes = [
            (
                record["enrollment_id"],
                evaluation["id"],
                self.table.item(row, col + 2).text(),
            )
            for row, record in enumerate(self.records)
            for col, evaluation in enumerate(self.evaluations)
        ]
        try:
            changed = self.store.record_grades(self.current_id, changes)
            self.dirty = False
            self.window.refresh()
            self.window.notify(f"{changed} calificaciones guardadas")
            return True
        except ValidationError as exc:
            self.window.notify(str(exc), True)
            return False

    def plan(self):
        if (
            self.current_id
            and self.can_leave()
            and PlanDialog(self.store, self.current_id, self).exec()
        ):
            self.window.refresh()


class HistoryPage(Page):
    def __init__(self, window):
        super().__init__(
            window,
            "Historial académico",
            "Cursos, ciclos y resultados de cada estudiante",
        )
        export = ActionButton("Exportar historial", "download")
        export.clicked.connect(lambda: self.export(student_id=self.student.currentData()))
        self.heading_actions.addWidget(export)
        tools = QHBoxLayout()
        tools.addWidget(label("Estudiante"))
        self.student = combo([])
        self.student.currentIndexChanged.connect(self.refresh_results)
        tools.addWidget(self.student, 1)
        self.body.addLayout(tools)
        self.info = label("", "notice", True)
        self.body.addWidget(self.info)
        stats = QHBoxLayout()
        self.stats = {}
        for key, title, symbol, color in [
            ("total", "Cursos inscritos", "book-open", "#147d70"),
            ("approved", "Cursos aprobados", "circle-check", "#32815a"),
            ("credits", "Créditos ganados", "graduation-cap", "#ad8a36"),
        ]:
            self.stats[key] = Stat(title, symbol, color)
            stats.addWidget(self.stats[key])
        self.body.addLayout(stats)
        self.table = DataTable(
            ["CICLO", "CÓDIGO", "CURSO", "PROFESOR", "CRÉDITOS", "NOTA", "RESULTADO"]
        )
        self.body.addWidget(self.table, 1)
        self.average = label("", "muted")
        self.body.addWidget(self.average)

    def refresh(self):
        update_combo(
            self.student,
            [(f"{s['code']} · {s['name']}", s["id"]) for s in self.store.people("students")],
        )
        self.refresh_results()

    def refresh_results(self):
        identifier = self.student.currentData()
        rows = self.store.results(student_id=identifier) if identifier else []
        self.table.fill(
            rows,
            [
                "cycle",
                "code",
                "course",
                "teacher",
                "credits",
                lambda r: f"{r['final']:.2f}",
                "status",
            ],
            "course_id",
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        approved = [r for r in rows if r["status"] == "APROBADO"]
        values = {
            "total": len(rows),
            "approved": len(approved),
            "credits": sum(r["credits"] for r in approved),
        }
        for key, widget in self.stats.items():
            widget.set_value(values[key], self.store.settings()["animations"])
        if identifier:
            student = self.store.require("students", identifier)
            self.info.setText(f"{student['career']}     ·     {student['email']}")
        else:
            self.info.setText("Sin estudiantes registrados")
        complete = [r for r in rows if r["status"] != "PENDIENTE"]
        credits = sum(r["credits"] for r in complete)
        average = sum(r["final"] * r["credits"] for r in complete) / credits if credits else None
        self.average.setText(
            f"Promedio de cursos completos, ponderado por créditos: {average:.2f}"
            if average is not None
            else "Promedio de cursos completos: pendiente"
        )


class SettingsPage(Page):
    def __init__(self, window):
        super().__init__(window, "Configuración", "Criterio académico, carátula y datos locales")
        save = ActionButton("Guardar configuración", "save", True)
        save.clicked.connect(self.save)
        self.heading_actions.addWidget(save)
        tabs = QTabWidget()
        self.body.addWidget(tabs, 1)
        academic = QWidget()
        academic_layout = QVBoxLayout(academic)
        academic_layout.setContentsMargins(0, 24, 0, 0)
        form = QFormLayout()
        form.setSpacing(18)
        self.passing = QDoubleSpinBox()
        self.passing.setRange(0, 100)
        self.passing.setDecimals(2)
        self.passing.setSuffix(" / 100")
        self.passing.setMaximumWidth(260)
        self.cycle = input_text()
        self.cycle.setMaximumWidth(380)
        self.animations = QCheckBox("Animaciones activadas")
        self.location = label(str(window.data_path), "muted", True)
        self.location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Nota mínima de aprobación", self.passing)
        form.addRow("Ciclo predeterminado", self.cycle)
        form.addRow("Interfaz", self.animations)
        form.addRow("Base de datos", self.location)
        academic_layout.addLayout(form)
        academic_layout.addSpacing(20)
        academic_layout.addWidget(label("Respaldo de información", "sectionTitle"))
        backup = ActionButton("Guardar respaldo", "database-backup")
        backup.setMaximumWidth(220)
        backup.clicked.connect(self.backup)
        academic_layout.addWidget(backup)
        academic_layout.addStretch()
        tabs.addTab(academic, "Criterio académico")
        cover_widget = QWidget()
        cover_layout = QVBoxLayout(cover_widget)
        cover_layout.setContentsMargins(0, 24, 20, 0)
        cover_form = QFormLayout()
        cover_form.setSpacing(13)
        self.cover = cover_fields(cover_form, self.store.settings()["cover"])
        cover_layout.addLayout(cover_form)
        cover_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cover_widget)
        tabs.addTab(scroll, "Carátula del proyecto")

    def refresh(self):
        values = self.store.settings()
        self.passing.setValue(values["passing"])
        self.cycle.setText(values["cycle"])
        self.animations.setChecked(values["animations"])
        for key, field in self.cover.items():
            if key == "members":
                field.setPlainText(values["cover"][key])
            else:
                field.setText(values["cover"][key])

    def save(self):
        self.attempt(
            lambda: self.store.save_settings(
                self.passing.value(),
                self.cycle.text(),
                self.animations.isChecked(),
                read_cover(self.cover),
            ),
            "Configuración guardada",
        )

    def backup(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar respaldo", "respaldo_siga.db", "Base de datos SQLite (*.db)"
        )
        if filename:
            self.attempt(lambda: self.store.backup(filename), "Respaldo guardado")
