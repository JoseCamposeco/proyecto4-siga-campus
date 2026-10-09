import os

import pytest

from siga.database import AcademicStore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def store(tmp_path):
    database = AcademicStore(tmp_path / "academic.db")
    yield database
    database.close()


@pytest.fixture
def academic(store):
    teacher = store.save_person(
        "teachers", "P-1", "Profesor Prueba", "profesor@ejemplo.edu", "Sistemas"
    )
    student = store.save_person(
        "students", "E-1", "Estudiante Prueba", "alumno@ejemplo.edu", "Ingeniería"
    )
    course = store.save_course("ALG-1", "Algoritmos", 5, "2026-II", teacher, 2)
    enrollment = store.enroll(student, course)
    return teacher, student, course, enrollment


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    from siga.theme import configure_app

    app = QApplication.instance() or QApplication([])
    configure_app(app)
    yield app
