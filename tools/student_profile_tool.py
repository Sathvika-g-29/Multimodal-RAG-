from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_STUDENT_DB_PATH = "data/extracted/student_profiles.csv"


@dataclass(frozen=True)
class StudentProfile:
    student_id: str
    cgpa: float
    backlogs: int
    branch: str | None = None


SAMPLE_STUDENT_PROFILES = {
    "22B01A0001": StudentProfile(student_id="22B01A0001", cgpa=7.2, backlogs=0, branch="CSE"),
    "22B01A0002": StudentProfile(student_id="22B01A0002", cgpa=6.8, backlogs=1, branch="IT"),
}


def fetch_student_profile(
    student_id: str,
    db_path: str | Path = DEFAULT_STUDENT_DB_PATH,
) -> StudentProfile | None:
    normalized_id = student_id.strip().upper()
    path = Path(db_path)
    if path.exists():
        frame = pd.read_csv(path)
        matches = frame[frame["student_id"].astype(str).str.upper() == normalized_id]
        if not matches.empty:
            row = matches.iloc[0]
            return StudentProfile(
                student_id=normalized_id,
                cgpa=float(row["cgpa"]),
                backlogs=int(row["backlogs"]),
                branch=str(row["branch"]) if "branch" in row else None,
            )

    return SAMPLE_STUDENT_PROFILES.get(normalized_id)

