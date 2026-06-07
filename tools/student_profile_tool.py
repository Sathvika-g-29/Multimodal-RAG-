import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path


DEFAULT_STUDENT_DB_PATH = Path("data/extracted/student_profiles.db")


@dataclass(frozen=True)
class StudentProfile:
    student_id: str
    cgpa: float
    backlogs: int
    branch: str | None = None


SAMPLE_STUDENT_PROFILES = [
    StudentProfile(student_id="22B01A0001", cgpa=7.2, backlogs=0, branch="CSE"),
    StudentProfile(student_id="22B01A0002", cgpa=6.8, backlogs=1, branch="IT"),
    StudentProfile(student_id="22B01A0003", cgpa=8.4, backlogs=0, branch="CSE"),
    StudentProfile(student_id="22B01A0004", cgpa=6.1, backlogs=2, branch="ECE"),
]


def initialize_student_db(db_path: str | Path = DEFAULT_STUDENT_DB_PATH) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS student_profiles (
                student_id TEXT PRIMARY KEY,
                cgpa REAL NOT NULL,
                backlogs INTEGER NOT NULL,
                branch TEXT
            )
            """
        )
    return path


def seed_student_db(
    profiles: list[StudentProfile] | None = None,
    db_path: str | Path = DEFAULT_STUDENT_DB_PATH,
) -> Path:
    path = initialize_student_db(db_path)
    records = profiles or SAMPLE_STUDENT_PROFILES
    with sqlite3.connect(path) as connection:
        connection.executemany(
            """
            INSERT OR REPLACE INTO student_profiles (student_id, cgpa, backlogs, branch)
            VALUES (?, ?, ?, ?)
            """,
            [
                (profile.student_id.upper(), profile.cgpa, profile.backlogs, profile.branch)
                for profile in records
            ],
        )
    return path


def fetch_student_profile(
    student_id: str,
    db_path: str | Path | None = None,
) -> StudentProfile | None:
    normalized_id = student_id.strip().upper()
    path = _resolve_db_path(db_path)
    if not path.exists():
        return None

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT student_id, cgpa, backlogs, branch
            FROM student_profiles
            WHERE UPPER(student_id) = ?
            """,
            (normalized_id,),
        ).fetchone()

    if not row:
        return None

    return StudentProfile(
        student_id=str(row["student_id"]).upper(),
        cgpa=float(row["cgpa"]),
        backlogs=int(row["backlogs"]),
        branch=str(row["branch"]) if row["branch"] else None,
    )


def _resolve_db_path(db_path: str | Path | None = None) -> Path:
    if db_path:
        return Path(db_path)
    return Path(os.getenv("STUDENT_DB_PATH", str(DEFAULT_STUDENT_DB_PATH)))
