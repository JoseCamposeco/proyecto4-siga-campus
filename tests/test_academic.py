import csv
import sqlite3

import pytest

from siga.database import AcademicStore, ValidationError, points


@pytest.mark.parametrize("value", [0, 100, "70", "69.99", "70,50"])
def test_valid_scores(value):
    assert 0 <= points(value) <= 10000


@pytest.mark.parametrize("value", [-1, 101, "NaN", "inf", "-Infinity", "hola", "", "50.001"])
def test_invalid_scores(value):
    with pytest.raises(ValidationError):
        points(value)


def test_duplicate_people_are_case_insensitive(store):
    store.save_person("students", "e-1", "Estudiante", "e@ejemplo.edu", "Sistemas")
    with pytest.raises(ValidationError):
        store.save_person("students", "E-1", "Otra persona", "otro@ejemplo.edu", "Sistemas")
    assert len(store.people("students")) == 1


@pytest.mark.parametrize(
    "code,name,email,career",
    [
        ("", "Nombre", "a@b.edu", "Sistemas"),
        ("CON ESPACIO", "Nombre", "a@b.edu", "Sistemas"),
        ("E1", "", "a@b.edu", "Sistemas"),
        ("E1", "Nombre", "correo", "Sistemas"),
        ("E1", "Nombre", "a@b.edu", ""),
    ],
)
def test_person_validation(store, code, name, email, career):
    with pytest.raises(ValidationError):
        store.save_person("students", code, name, email, career)


def test_modify_person_and_search(store, academic):
    _, student, _, _ = academic
    store.save_person(
        "students", "E-1", "Nombre actualizado", "nuevo@ejemplo.edu", "Informática", student
    )
    assert store.people("students", "ACTUALIZADO")[0]["name"] == "Nombre actualizado"
    assert len(store.people("students", "e-1")) == 1


def test_duplicate_enrollment(store, academic):
    _, student, course, _ = academic
    with pytest.raises(ValidationError, match="ya está inscrito"):
        store.enroll(student, course)
    assert len(store.results(course_id=course)) == 1


def test_capacity(store, academic):
    _, _, course, _ = academic
    for code in ["E2", "E3"]:
        student = store.save_person("students", code, code, code + "@ejemplo.edu", "Sistemas")
        if code == "E2":
            store.enroll(student, course)
        else:
            with pytest.raises(ValidationError, match="cupo máximo"):
                store.enroll(student, course)


def test_professor_required_and_reassignment(store, academic):
    _, _, course, _ = academic
    with pytest.raises(ValidationError):
        store.save_course("BAD", "Curso", 5, "2026-II", 9999, 40)
    teacher = store.save_person("teachers", "P2", "Profesor Nuevo", "p2@ejemplo.edu", "Sistemas")
    store.save_course("ALG-1", "Algoritmos", 5, "2026-II", teacher, 2, course)
    assert store.courses()[0]["teacher"] == "Profesor Nuevo"


@pytest.mark.parametrize("credits,capacity", [(0, 10), (31, 10), (5.5, 10), (5, 0), (5, 1001)])
def test_invalid_course_limits(store, academic, credits, capacity):
    teacher, _, _, _ = academic
    with pytest.raises(ValidationError):
        store.save_course("X", "Curso", credits, "2026-II", teacher, capacity)


def test_evaluation_plan_validation(store, academic):
    _, _, course, _ = academic
    original = store.evaluations(course)
    for entries in [[("A", 60), ("B", 30)], [("A", 50), ("a", 50)], [("A", 0), ("B", 100)], []]:
        with pytest.raises(ValidationError):
            store.set_evaluation_plan(course, entries)
        assert store.evaluations(course) == original
    store.set_evaluation_plan(course, [("Trabajo", 30), ("Final", 70)])
    assert [e["weight"] for e in store.evaluations(course)] == [3000, 7000]


def test_weighted_grade_modify_and_audit(store, academic):
    _, student, course, enrollment = academic
    evaluations = store.evaluations(course)
    values = [60, 70, 80, 90]
    assert (
        store.record_grades(
            course, [(enrollment, e["id"], value) for e, value in zip(evaluations, values)]
        )
        == 4
    )
    result = store.results(student_id=student)[0]
    assert result["final"] == 78
    assert result["status"] == "APROBADO"
    store.record_grades(course, [(enrollment, evaluations[-1]["id"], 50)])
    assert store.results()[0]["final"] == 62
    assert store.results()[0]["status"] == "REPROBADO"
    assert store.activity()[0]["action"] == "Calificación modificada"
    with pytest.raises(ValidationError, match="notas registradas"):
        store.set_evaluation_plan(course, [("Final", 100)])


@pytest.mark.parametrize(
    "value,status", [(0, "REPROBADO"), (69.99, "REPROBADO"), (70, "APROBADO"), (100, "APROBADO")]
)
def test_threshold_boundaries(store, academic, value, status):
    _, _, course, enrollment = academic
    store.record_grades(course, [(enrollment, e["id"], value) for e in store.evaluations(course)])
    assert store.results()[0]["status"] == status


def test_rounding_matches_displayed_approval(store, academic):
    _, _, course, enrollment = academic
    evaluations = store.evaluations(course)
    store.record_grades(
        course,
        [(enrollment, e["id"], 70 if index != 0 else 69.98) for index, e in enumerate(evaluations)],
    )
    result = store.results()[0]
    assert result["final"] == 70.00
    assert result["status"] == "APROBADO"


def test_sql_capacity_guard(store, academic):
    _, _, course, _ = academic
    for index in range(2):
        student = store.save_person(
            "students", f"SQL{index}", "Alumno", f"sql{index}@ejemplo.edu", "Sistemas"
        )
        if index == 0:
            store.enroll(student, course)
        else:
            with pytest.raises(sqlite3.IntegrityError, match="full_course"):
                with store.db:
                    store.db.execute(
                        "INSERT INTO enrollments(student_id,course_id) VALUES(?,?)",
                        (student, course),
                    )


def test_incomplete_is_pending_and_zero_is_a_grade(store, academic):
    _, _, course, enrollment = academic
    evaluation = store.evaluations(course)[0]
    store.record_grades(course, [(enrollment, evaluation["id"], 0)])
    result = store.results()[0]
    assert result["completed"] == 1
    assert result["status"] == "PENDIENTE"
    store.record_grades(course, [(enrollment, evaluation["id"], "")])
    assert store.results()[0]["completed"] == 0


def test_invalid_batch_writes_nothing(store, academic):
    _, _, course, enrollment = academic
    a, b, *_ = store.evaluations(course)
    with pytest.raises(ValidationError):
        store.record_grades(course, [(enrollment, a["id"], 90), (enrollment, b["id"], 101)])
    assert store.results()[0]["completed"] == 0


def test_cross_course_grade_rejected(store, academic):
    teacher, student, course, enrollment = academic
    other = store.save_course("OTRO", "Otro curso", 4, "2026-II", teacher, 10)
    store.enroll(student, other)
    with pytest.raises(ValidationError, match="mismo curso"):
        store.record_grades(course, [(enrollment, store.evaluations(other)[0]["id"], 70)])


def test_history_preserves_cycles(store, academic):
    teacher, student, _, _ = academic
    next_course = store.save_course("ALG-1", "Algoritmos", 5, "2027-I", teacher, 40)
    store.enroll(student, next_course)
    assert {row["cycle"] for row in store.results(student_id=student)} == {"2026-II", "2027-I"}


def test_close_course_and_correct_complete_grades(store, academic):
    _, student, course, enrollment = academic
    with pytest.raises(ValidationError):
        store.close_course(course)
    evaluations = store.evaluations(course)
    store.record_grades(course, [(enrollment, e["id"], 70) for e in evaluations])
    store.close_course(course)
    store.record_grades(course, [(enrollment, evaluations[0]["id"], 60)])
    assert store.results()[0]["status"] == "REPROBADO"
    previous = store.results()[0]["final"]
    with pytest.raises(ValidationError):
        store.record_grades(
            course, [(enrollment, evaluations[0]["id"], 90), (enrollment, evaluations[1]["id"], "")]
        )
    assert store.results()[0]["final"] == previous
    other = store.save_person("students", "E2", "Otro", "otro@ejemplo.edu", "Sistemas")
    with pytest.raises(ValidationError, match="cerrado"):
        store.enroll(other, course)
    assert len(store.results(student_id=student)) == 1


def test_settings_recalculate_results(store, academic):
    _, _, course, enrollment = academic
    store.record_grades(course, [(enrollment, e["id"], 65) for e in store.evaluations(course)])
    settings = store.settings()
    store.save_settings(60, "2027-I", False, settings["cover"])
    assert store.results()[0]["status"] == "APROBADO"
    assert store.settings()["passing"] == 60
    with pytest.raises(ValidationError):
        store.save_settings(101, "2027-I", False, settings["cover"])
    assert store.settings()["passing"] == 60


def test_backup_and_persistence(store, academic, tmp_path):
    backup = tmp_path / "backup.db"
    store.backup(backup)
    restored = AcademicStore(backup)
    assert restored.dashboard() == store.dashboard()
    assert restored.query("PRAGMA integrity_check")[0]["integrity_check"] == "ok"
    restored.close()
    with pytest.raises(ValidationError):
        store.backup(store.path)
    assert AcademicStore(store.path).people("students")[0]["code"] == "E-1"


def test_export_csv_and_formula_protection(store, academic, tmp_path):
    _, student, _, _ = academic
    store.save_person("students", "E-1", "=FORMULA()", "x@ejemplo.edu", "Sistemas", student)
    target = tmp_path / "results.csv"
    assert store.export_results(target, student_id=student) == 1
    with target.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[1][1] == "'=FORMULA()"
    assert rows[1][-1] == "PENDIENTE"


def test_database_constraints(store, academic):
    _, student, course, _ = academic
    with pytest.raises(sqlite3.IntegrityError):
        with store.db:
            store.db.execute(
                "INSERT INTO enrollments(student_id,course_id) VALUES(?,?)", (student, course)
            )
    with pytest.raises(sqlite3.IntegrityError):
        with store.db:
            store.db.execute("INSERT INTO enrollments(student_id,course_id) VALUES(999,999)")


def test_demo_and_cover(store):
    assert store.settings()["passing"] == 70
    assert "José Gabriel Camposeco Santizo" in store.settings()["cover"]["members"]
    store.load_demo()
    assert store.dashboard()["enrollments"] == 27
    assert store.dashboard()["courses"] == 4
    with pytest.raises(ValidationError):
        store.load_demo()
