from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialogButtonBox, QLineEdit

from siga.app import MainWindow
from siga.dialogs import CoverDialog, PersonDialog
from siga.widgets import icon


def test_cover_has_correct_members_and_opens(qapp, store):
    cover = CoverDialog(store)
    cover.show()
    qapp.processEvents()
    assert cover.enter.isVisible()
    QTest.mouseClick(cover.enter, Qt.MouseButton.LeftButton)
    assert cover.result() == CoverDialog.DialogCode.Accepted
    assert len(store.settings()["cover"]["members"].splitlines()) == 4


def test_registration_modal_validation_then_save(qapp, store):
    window = MainWindow(store, store.path)
    dialog = PersonDialog(store, "students", window)
    dialog.show()
    button = dialog.buttons.button(QDialogButtonBox.StandardButton.Save)
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert dialog.error.isVisible()
    for name, value in [
        ("code", "GUI-1"),
        ("name", "Alumno GUI"),
        ("email", "gui@ejemplo.edu"),
        ("career", "Sistemas"),
    ]:
        dialog.findChild(QLineEdit, name).setText(value)
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert len(store.people("students")) == 1
    window.close()


def test_all_pages_and_grade_edit_recalculates(qapp, store, academic):
    _, student, course, _ = academic
    window = MainWindow(store, store.path)
    window.show()
    for key in window.pages:
        assert window.navigate(key)
        QTest.qWait(5)
        assert window.stack.currentWidget() is window.pages[key]
    window.open_course(course, "grades")
    grades = window.pages["grades"]
    for col in range(2, 6):
        grades.table.item(0, col).setText("70")
    assert grades.dirty
    QTest.mouseClick(grades.save_button, Qt.MouseButton.LeftButton)
    assert not grades.dirty
    assert store.results()[0]["status"] == "APROBADO"
    grades.table.item(0, 2).setText("0")
    assert grades.save()
    assert store.results()[0]["status"] == "REPROBADO"
    window.open_student(student)
    assert window.pages["history"].table.rowCount() == 1
    window.close()


def test_grade_ui_invalid_batch_keeps_dirty(qapp, store, academic):
    _, _, course, _ = academic
    window = MainWindow(store, store.path)
    window.open_course(course, "grades")
    grades = window.pages["grades"]
    grades.table.item(0, 2).setText("101")
    assert not grades.save()
    assert grades.dirty
    assert store.results()[0]["completed"] == 0
    grades.dirty = False
    window.close()


def test_icons_are_present():
    for name in ["graduation-cap", "save", "users", "pencil", "download", "book-open"]:
        assert not icon(name).isNull()
