import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    name TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    schedule TEXT NOT NULL,
    max_participants INTEGER NOT NULL CHECK (max_participants > 0)
);

CREATE TABLE IF NOT EXISTS students (
    email TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS enrollments (
    activity_name TEXT NOT NULL,
    student_email TEXT NOT NULL,
    PRIMARY KEY (activity_name, student_email),
    FOREIGN KEY (activity_name) REFERENCES activities(name) ON DELETE CASCADE,
    FOREIGN KEY (student_email) REFERENCES students(email) ON DELETE CASCADE
);
"""


class ActivityStorage:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self, seed_activities: dict) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            activity_count = connection.execute(
                "SELECT COUNT(*) FROM activities"
            ).fetchone()[0]
            if activity_count:
                return

            for name, details in seed_activities.items():
                connection.execute(
                    """
                    INSERT INTO activities (name, description, schedule, max_participants)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        name,
                        details["description"],
                        details["schedule"],
                        details["max_participants"],
                    ),
                )
                for email in details["participants"]:
                    connection.execute(
                        "INSERT OR IGNORE INTO students (email) VALUES (?)",
                        (email,),
                    )
                    connection.execute(
                        """
                        INSERT INTO enrollments (activity_name, student_email)
                        VALUES (?, ?)
                        """,
                        (name, email),
                    )

    def get_activities(self) -> dict:
        with self._connect() as connection:
            activity_rows = connection.execute(
                """
                SELECT name, description, schedule, max_participants
                FROM activities
                ORDER BY rowid
                """
            ).fetchall()
            enrollment_rows = connection.execute(
                """
                SELECT activity_name, student_email
                FROM enrollments
                ORDER BY rowid
                """
            ).fetchall()

        participants = {row["name"]: [] for row in activity_rows}
        for row in enrollment_rows:
            participants[row["activity_name"]].append(row["student_email"])

        return {
            row["name"]: {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": participants[row["name"]],
            }
            for row in activity_rows
        }

    def activity_exists(self, activity_name: str) -> bool:
        with self._connect() as connection:
            return connection.execute(
                "SELECT 1 FROM activities WHERE name = ?",
                (activity_name,),
            ).fetchone() is not None

    def signup(self, activity_name: str, email: str) -> bool:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO students (email) VALUES (?)",
                (email,),
            )
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO enrollments (activity_name, student_email)
                VALUES (?, ?)
                """,
                (activity_name, email),
            )
            return cursor.rowcount == 1

    def unregister(self, activity_name: str, email: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM enrollments
                WHERE activity_name = ? AND student_email = ?
                """,
                (activity_name, email),
            )
            return cursor.rowcount == 1