"""Persistencia y reglas academicas; no depende de la interfaz grafica."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from contextlib import contextmanager
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path


class ValidationError(ValueError):
    """Operacion que viola una regla del sistema."""


DEFAULT_COVER = {
    "university": "Universidad: pendiente de completar",
    "career": "INGENIERÍA EN SISTEMAS",
    "subject": "ALGORITMOS",
    "teacher": "DEMSHILL LEONEL COUTIÑO SANDOVAL",
    "team": "Equipo: pendiente de completar",
    "members": "José Gabriel Camposeco Santizo\nAXEL MIGUEL ESTRADA GARCÍA\nDAFHNE XIMENA GABRIEL ESCOBAR\nCRISTOFHER OMAR MUÑOZ ESCOBAR",
}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS students(
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE COLLATE NOCASE,
 name TEXT NOT NULL, email TEXT NOT NULL, career TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS teachers(
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE COLLATE NOCASE,
 name TEXT NOT NULL, email TEXT NOT NULL, specialty TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS courses(
 id INTEGER PRIMARY KEY, code TEXT NOT NULL COLLATE NOCASE, name TEXT NOT NULL,
 credits INTEGER NOT NULL CHECK(credits BETWEEN 1 AND 30), cycle TEXT NOT NULL,
 teacher_id INTEGER NOT NULL REFERENCES teachers(id),
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 1000),
 closed INTEGER NOT NULL DEFAULT 0 CHECK(closed IN (0,1)), UNIQUE(code,cycle));
CREATE TABLE IF NOT EXISTS enrollments(
 id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id),
 course_id INTEGER NOT NULL REFERENCES courses(id),
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now')),
 UNIQUE(student_id,course_id));
CREATE TABLE IF NOT EXISTS evaluations(
 id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL REFERENCES courses(id),
 name TEXT NOT NULL, weight INTEGER NOT NULL CHECK(weight BETWEEN 1 AND 10000),
 UNIQUE(course_id,name));
CREATE TABLE IF NOT EXISTS grades(
 enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
 evaluation_id INTEGER NOT NULL REFERENCES evaluations(id),
 score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 10000),
 PRIMARY KEY(enrollment_id,evaluation_id));
CREATE TABLE IF NOT EXISTS audit(
 id INTEGER PRIMARY KEY, action TEXT NOT NULL, detail TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now')));
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_course ON evaluations(course_id);
CREATE TRIGGER IF NOT EXISTS enforce_enrollment_capacity
BEFORE INSERT ON enrollments BEGIN
 SELECT CASE WHEN (SELECT closed FROM courses WHERE id=NEW.course_id)=1
 THEN RAISE(ABORT,'closed_course') END;
 SELECT CASE WHEN (SELECT COUNT(*) FROM enrollments WHERE course_id=NEW.course_id)
 >= (SELECT capacity FROM courses WHERE id=NEW.course_id)
 THEN RAISE(ABORT,'full_course') END;
END;
"""


def clean_text(value, label, maximum=120):
    text = str(value).strip()
    if not text or len(text) > maximum:
        raise ValidationError(f"{label}: escribe entre 1 y {maximum} caracteres.")
    if any(ord(char) < 32 for char in text):
        raise ValidationError(f"{label}: no se permiten caracteres de control.")
    return text


def points(value, label="Nota", minimum=0, maximum=100):
    try:
        number = Decimal(str(value).strip().replace(",", "."))
        if not number.is_finite() or not Decimal(minimum) <= number <= Decimal(maximum):
            raise InvalidOperation
        if number != number.quantize(Decimal("0.01")):
            raise ValidationError(f"{label}: utiliza como máximo dos decimales.")
        return int(number * 100)
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{label}: debe estar entre {minimum} y {maximum}.") from None


def integer(value, label, minimum, maximum):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number != int(number) or not minimum <= number <= maximum:
            raise ValueError
        return int(number)
    except (InvalidOperation, ValueError, OverflowError):
        raise ValidationError(f"{label}: ingresa un entero de {minimum} a {maximum}.") from None


class AcademicStore:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO settings VALUES('passing','70')")
            self.db.execute("INSERT OR IGNORE INTO settings VALUES('cycle','2026-II')")
            self.db.execute("INSERT OR IGNORE INTO settings VALUES('animations','true')")
            self.db.execute(
                "INSERT OR IGNORE INTO settings VALUES('cover',?)",
                (json.dumps(DEFAULT_COVER, ensure_ascii=False),),
            )

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        try:
            with self.db:
                yield
        except sqlite3.IntegrityError as exc:
            if str(exc) == "full_course":
                raise ValidationError("El curso alcanzó su cupo máximo.") from None
            if str(exc) == "closed_course":
                raise ValidationError("El curso está cerrado.") from None
            if "UNIQUE" in str(exc):
                raise ValidationError(
                    "Ese código o registro ya existe. No se permiten duplicados."
                ) from None
            raise ValidationError(
                "La operación no cumple las relaciones o límites establecidos."
            ) from None

    def query(self, sql, args=()):
        return [dict(row) for row in self.db.execute(sql, args)]

    def get_setting(self, key):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def settings(self):
        return {
            "passing": float(self.get_setting("passing")),
            "cycle": self.get_setting("cycle"),
            "animations": self.get_setting("animations") == "true",
            "cover": json.loads(self.get_setting("cover")),
        }

    def save_settings(self, passing, cycle, animations, cover):
        threshold = points(passing, "Nota de aprobación") / 100
        cycle = clean_text(cycle, "Ciclo", 30)
        if set(cover) != set(DEFAULT_COVER):
            raise ValidationError("La carátula debe contener todos los campos.")
        sanitized = {}
        for key, value in cover.items():
            if key == "members":
                lines = [
                    clean_text(line, "Integrante", 180)
                    for line in value.splitlines()
                    if line.strip()
                ]
                if not 1 <= len(lines) <= 20:
                    raise ValidationError("Agrega entre 1 y 20 integrantes.")
                sanitized[key] = "\n".join(lines)
            else:
                sanitized[key] = clean_text(value, "Datos de carátula", 180)
        with self.transaction():
            for key, value in [
                ("passing", str(threshold)),
                ("cycle", cycle),
                ("animations", json.dumps(bool(animations))),
                ("cover", json.dumps(sanitized, ensure_ascii=False)),
            ]:
                self.db.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
            self.log(
                "Configuración actualizada",
                f"Aprobación desde {threshold:g} puntos; ciclo {cycle}",
            )

    def log(self, action, detail):
        self.db.execute("INSERT INTO audit(action,detail) VALUES(?,?)", (action, detail))

    def require(self, table, identifier):
        if table not in {
            "students",
            "teachers",
            "courses",
            "enrollments",
            "evaluations",
        }:
            raise ValueError("Tabla desconocida")
        row = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValidationError("El registro seleccionado ya no existe.")
        return dict(row)

    def save_person(self, kind, code, name, email, field, identifier=None):
        if kind not in {"students", "teachers"}:
            raise ValueError("Tipo de persona desconocido")
        code = clean_text(code, "Código", 30).upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", code):
            raise ValidationError("Código: utiliza letras, números, puntos o guiones.")
        name = clean_text(name, "Nombre")
        email = clean_text(email, "Correo", 180)
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValidationError("Ingresa un correo electrónico válido.")
        field = clean_text(field, "Carrera" if kind == "students" else "Especialidad")
        extra = "career" if kind == "students" else "specialty"
        with self.transaction():
            if identifier is None:
                cursor = self.db.execute(
                    f"INSERT INTO {kind}(code,name,email,{extra}) VALUES(?,?,?,?)",
                    (code, name, email, field),
                )
                identifier = cursor.lastrowid
            else:
                self.require(kind, identifier)
                self.db.execute(
                    f"UPDATE {kind} SET code=?,name=?,email=?,{extra}=? WHERE id=?",
                    (code, name, email, field, identifier),
                )
            self.log(
                "Estudiante actualizado" if kind == "students" else "Profesor actualizado",
                f"{code} · {name}",
            )
        return identifier

    def people(self, kind, search=""):
        if kind not in {"students", "teachers"}:
            raise ValueError("Tipo desconocido")
        rows = self.query(f"SELECT * FROM {kind} ORDER BY name COLLATE NOCASE")
        text = search.casefold().strip()
        return [r for r in rows if text in " ".join(str(v) for v in r.values()).casefold()]

    def save_course(self, code, name, credits, cycle, teacher_id, capacity, identifier=None):
        code = clean_text(code, "Código", 30).upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", code):
            raise ValidationError("Código de curso inválido.")
        name = clean_text(name, "Nombre del curso")
        cycle = clean_text(cycle, "Ciclo", 30)
        credits = integer(credits, "Créditos", 1, 30)
        capacity = integer(capacity, "Cupo", 1, 1000)
        self.require("teachers", teacher_id)
        with self.transaction():
            values = (code, name, credits, cycle, teacher_id, capacity)
            if identifier is None:
                identifier = self.db.execute(
                    "INSERT INTO courses(code,name,credits,cycle,teacher_id,capacity) VALUES(?,?,?,?,?,?)",
                    values,
                ).lastrowid
                for title, weight in [
                    ("Parcial 1", 2000),
                    ("Parcial 2", 2000),
                    ("Actividades", 2000),
                    ("Examen final", 4000),
                ]:
                    self.db.execute(
                        "INSERT INTO evaluations(course_id,name,weight) VALUES(?,?,?)",
                        (identifier, title, weight),
                    )
            else:
                current = self.require("courses", identifier)
                count = self.db.execute(
                    "SELECT COUNT(*) FROM enrollments WHERE course_id=?", (identifier,)
                ).fetchone()[0]
                if current["closed"]:
                    raise ValidationError(
                        "El curso está cerrado; sus datos académicos están protegidos."
                    )
                if capacity < count:
                    raise ValidationError("El cupo no puede ser menor al número de inscritos.")
                if count and cycle != current["cycle"]:
                    raise ValidationError("Un curso con inscripciones no puede cambiar de ciclo.")
                self.db.execute(
                    "UPDATE courses SET code=?,name=?,credits=?,cycle=?,teacher_id=?,capacity=? WHERE id=?",
                    (*values, identifier),
                )
            self.log("Curso actualizado", f"{code} · {name} · {cycle}")
        return identifier

    def courses(self, search=""):
        rows = self.query("""SELECT c.*, t.name AS teacher,
            (SELECT COUNT(*) FROM enrollments e WHERE e.course_id=c.id) AS enrolled
            FROM courses c JOIN teachers t ON t.id=c.teacher_id ORDER BY c.cycle DESC,c.name""")
        return [
            r
            for r in rows
            if search.casefold().strip() in " ".join(str(v) for v in r.values()).casefold()
        ]

    def enroll(self, student_id, course_id):
        student = self.require("students", student_id)
        course = self.require("courses", course_id)
        with self.transaction():
            if self.db.execute(
                "SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?",
                (student_id, course_id),
            ).fetchone():
                raise ValidationError("El estudiante ya está inscrito en este curso y ciclo.")
            if course["closed"]:
                raise ValidationError("El curso está cerrado y no admite inscripciones.")
            count = self.db.execute(
                "SELECT COUNT(*) FROM enrollments WHERE course_id=?", (course_id,)
            ).fetchone()[0]
            if count >= course["capacity"]:
                raise ValidationError("El curso alcanzó su cupo máximo.")
            if sum(e["weight"] for e in self.evaluations(course_id)) != 10000:
                raise ValidationError("El plan de evaluación debe sumar 100 % antes de inscribir.")
            identifier = self.db.execute(
                "INSERT INTO enrollments(student_id,course_id) VALUES(?,?)",
                (student_id, course_id),
            ).lastrowid
            self.log("Inscripción registrada", f"{student['name']} · {course['name']}")
        return identifier

    def evaluations(self, course_id):
        return self.query("SELECT * FROM evaluations WHERE course_id=? ORDER BY id", (course_id,))

    def set_evaluation_plan(self, course_id, entries):
        course = self.require("courses", course_id)
        if course["closed"]:
            raise ValidationError("No se puede cambiar el plan de un curso cerrado.")
        normalized = [
            (
                clean_text(name, "Evaluación", 80),
                points(weight, "Ponderación", minimum=0.01),
            )
            for name, weight in entries
        ]
        if not 1 <= len(normalized) <= 12:
            raise ValidationError("El plan debe tener entre 1 y 12 evaluaciones.")
        if len({n.casefold() for n, _ in normalized}) != len(normalized):
            raise ValidationError("Las evaluaciones deben tener nombres distintos.")
        if sum(w for _, w in normalized) != 10000:
            raise ValidationError("Las ponderaciones deben sumar exactamente 100 %.")
        with self.transaction():
            if self.db.execute(
                "SELECT 1 FROM grades g JOIN evaluations e ON e.id=g.evaluation_id WHERE e.course_id=?",
                (course_id,),
            ).fetchone():
                raise ValidationError("El plan ya tiene notas registradas y no puede reemplazarse.")
            self.db.execute("DELETE FROM evaluations WHERE course_id=?", (course_id,))
            self.db.executemany(
                "INSERT INTO evaluations(course_id,name,weight) VALUES(?,?,?)",
                [(course_id, n, w) for n, w in normalized],
            )
            self.log("Plan de evaluación actualizado", course["name"])

    def record_grades(self, course_id, changes):
        """Validate the entire batch before writing, so one invalid cell rolls back all."""
        course = self.require("courses", course_id)
        normalized = []
        seen = set()
        for enrollment_id, evaluation_id, value in changes:
            enrollment = self.require("enrollments", enrollment_id)
            evaluation = self.require("evaluations", evaluation_id)
            if enrollment["course_id"] != course_id or evaluation["course_id"] != course_id:
                raise ValidationError(
                    "La evaluación y la inscripción deben pertenecer al mismo curso."
                )
            if (enrollment_id, evaluation_id) in seen:
                raise ValidationError("La misma nota aparece dos veces en el lote.")
            seen.add((enrollment_id, evaluation_id))
            score = None if value is None or str(value).strip() == "" else points(value)
            normalized.append((enrollment_id, evaluation_id, score))
        with self.transaction():
            changed = 0
            for enrollment_id, evaluation_id, score in normalized:
                old = self.db.execute(
                    "SELECT score FROM grades WHERE enrollment_id=? AND evaluation_id=?",
                    (enrollment_id, evaluation_id),
                ).fetchone()
                previous = old[0] if old else None
                if score == previous:
                    continue
                if score is None and course["closed"]:
                    raise ValidationError(
                        "Un curso cerrado requiere todas sus notas; no se puede borrar una."
                    )
                if score is None:
                    self.db.execute(
                        "DELETE FROM grades WHERE enrollment_id=? AND evaluation_id=?",
                        (enrollment_id, evaluation_id),
                    )
                else:
                    self.db.execute(
                        "INSERT INTO grades VALUES(?,?,?) ON CONFLICT(enrollment_id,evaluation_id) DO UPDATE SET score=excluded.score",
                        (enrollment_id, evaluation_id, score),
                    )
                self.log(
                    "Calificación modificada" if old else "Calificación registrada",
                    f"{course['name']} · inscripción {enrollment_id} · "
                    f"{self.require('evaluations', evaluation_id)['name']}: "
                    f"{previous / 100 if previous is not None else 'Sin nota'} -> "
                    f"{score / 100 if score is not None else 'Sin nota'}",
                )
                changed += 1
        return changed

    def results(self, course_id=None, student_id=None):
        sql = """SELECT e.id AS enrollment_id,e.student_id,e.course_id,s.code AS student_code,
            s.name AS student,c.code,c.name AS course,c.cycle,c.credits,c.closed,t.name AS teacher
            FROM enrollments e JOIN students s ON s.id=e.student_id
            JOIN courses c ON c.id=e.course_id JOIN teachers t ON t.id=c.teacher_id WHERE 1=1"""
        args = []
        if course_id is not None:
            sql += " AND e.course_id=?"
            args.append(course_id)
        if student_id is not None:
            sql += " AND e.student_id=?"
            args.append(student_id)
        rows = self.query(sql + " ORDER BY c.cycle DESC,c.name,s.name", args)
        passing = Decimal(self.get_setting("passing"))
        for row in rows:
            evaluations = self.evaluations(row["course_id"])
            grades = {
                g["evaluation_id"]: g["score"]
                for g in self.query(
                    "SELECT * FROM grades WHERE enrollment_id=?",
                    (row["enrollment_id"],),
                )
            }
            total = sum(grades.get(e["id"], 0) * e["weight"] for e in evaluations)
            raw = Decimal(total) / Decimal(1000000)
            final = raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            row["final"] = float(final)
            row["completed"] = len(grades)
            row["evaluations"] = len(evaluations)
            row["grades"] = {key: value / 100 for key, value in grades.items()}
            complete = (
                bool(evaluations)
                and len(grades) == len(evaluations)
                and sum(e["weight"] for e in evaluations) == 10000
            )
            row["status"] = (
                ("APROBADO" if final >= passing else "REPROBADO") if complete else "PENDIENTE"
            )
        return rows

    def close_course(self, course_id):
        course = self.require("courses", course_id)
        if sum(e["weight"] for e in self.evaluations(course_id)) != 10000:
            raise ValidationError("El plan de evaluación debe sumar 100 %.")
        results = self.results(course_id=course_id)
        if not results or any(r["status"] == "PENDIENTE" for r in results):
            raise ValidationError(
                "Para cerrar, inscribe estudiantes y completa todas las calificaciones."
            )
        with self.transaction():
            self.db.execute("UPDATE courses SET closed=1 WHERE id=?", (course_id,))
            self.log("Curso cerrado", f"{course['name']} · {course['cycle']}")

    def dashboard(self):
        results = self.results()
        return {
            "students": len(self.people("students")),
            "teachers": len(self.people("teachers")),
            "courses": len(self.courses()),
            "enrollments": len(results),
            "approved": sum(r["status"] == "APROBADO" for r in results),
            "failed": sum(r["status"] == "REPROBADO" for r in results),
            "pending": sum(r["status"] == "PENDIENTE" for r in results),
        }

    def activity(self, limit=10):
        return self.query("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,))

    def backup(self, target):
        if self.path != ":memory:" and Path(target).resolve() == Path(self.path).resolve():
            raise ValidationError(
                "El respaldo debe guardarse en un archivo distinto de la base activa."
            )
        with sqlite3.connect(str(target)) as backup_db:
            self.db.backup(backup_db)

    def export_results(self, path, course_id=None, student_id=None):
        rows = self.results(course_id, student_id)
        headers = [
            ("student_code", "Carné"),
            ("student", "Estudiante"),
            ("code", "Código de curso"),
            ("course", "Curso"),
            ("cycle", "Ciclo"),
            ("teacher", "Profesor"),
            ("final", "Nota acumulada / final"),
            ("status", "Estado"),
        ]

        def safe(value):
            text = str(value)
            return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text

        with open(path, "w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow([label for _, label in headers])
            writer.writerows([[safe(row[key]) for key, _ in headers] for row in rows])
        return len(rows)

    def load_demo(self):
        if any(self.dashboard()[key] for key in ("students", "teachers", "courses")):
            raise ValidationError("La demostración solo se puede cargar en una base vacía.")
        teachers = [
            self.save_person("teachers", f"P00{i + 1}", name, f"docente{i + 1}@ejemplo.edu", field)
            for i, (name, field) in enumerate(
                [
                    ("Elena Morales", "Programación"),
                    ("Ricardo Fuentes", "Matemática"),
                    ("Valeria Ortiz", "Ciencias de datos"),
                ]
            )
        ]
        students = [
            self.save_person(
                "students",
                f"2026-{i + 1:03}",
                name,
                f"estudiante{i + 1}@ejemplo.edu",
                "Ingeniería en Sistemas",
            )
            for i, name in enumerate(
                [
                    "Ana Lucía Pérez",
                    "Carlos Méndez",
                    "María Fernanda López",
                    "Diego Hernández",
                    "Sofía Ramírez",
                    "Luis Andrés Torres",
                    "Camila Ruiz",
                    "Mateo Castillo",
                ]
            )
        ]
        courses = [
            self.save_course(code, name, credits, "2026-II", teachers[i % 3], 30)
            for i, (code, name, credits) in enumerate(
                [
                    ("ALG-101", "Algoritmos", 5),
                    ("MAT-102", "Matemática discreta", 4),
                    ("PRO-103", "Programación I", 5),
                    ("DAT-104", "Fundamentos de datos", 4),
                ]
            )
        ]
        for index, course_id in enumerate(courses):
            evaluations = self.evaluations(course_id)
            for j, student_id in enumerate(students[: 6 + index % 3]):
                enrollment = self.enroll(student_id, course_id)
                count = 4 if index == 0 else 2 + j % 3
                scores = [55, 68, 87, 93, 74, 82, 65, 90]
                self.record_grades(
                    course_id,
                    [
                        (enrollment, e["id"], min(100, scores[j] + k * 2))
                        for k, e in enumerate(evaluations[:count])
                    ],
                )
        self.close_course(courses[0])
