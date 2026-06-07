import argparse

from tools.student_profile_tool import DEFAULT_STUDENT_DB_PATH, seed_student_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and seed the local student profile database.")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_STUDENT_DB_PATH),
        help="SQLite database path for student profiles.",
    )
    args = parser.parse_args()

    path = seed_student_db(db_path=args.db)
    print(f"Seeded student profile database at {path}")


if __name__ == "__main__":
    main()
