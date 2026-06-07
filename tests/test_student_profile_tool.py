from tools.student_profile_tool import StudentProfile, fetch_student_profile, seed_student_db


def test_seed_and_fetch_student_profile(tmp_path) -> None:
    db_path = tmp_path / "students.db"
    seed_student_db(
        profiles=[StudentProfile(student_id="22B01A9999", cgpa=8.1, backlogs=0, branch="CSE")],
        db_path=db_path,
    )

    profile = fetch_student_profile("22b01a9999", db_path=db_path)

    assert profile is not None
    assert profile.student_id == "22B01A9999"
    assert profile.cgpa == 8.1
    assert profile.backlogs == 0
    assert profile.branch == "CSE"


def test_fetch_student_profile_returns_none_for_missing_db(tmp_path) -> None:
    profile = fetch_student_profile("22B01A9999", db_path=tmp_path / "missing.db")

    assert profile is None
