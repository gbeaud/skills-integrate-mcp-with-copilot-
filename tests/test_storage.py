import tempfile
import unittest
from pathlib import Path

from src.storage import ActivityStorage


SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Play chess",
        "schedule": "Fridays",
        "max_participants": 12,
        "participants": ["member@mergington.edu"],
    }
}


class ActivityStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "activities.db"
        self.storage = ActivityStorage(self.database_path)
        self.storage.initialize(SEED_ACTIVITIES)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_seed_data_and_enrollment_persist_across_storage_instances(self):
        self.assertTrue(
            self.storage.signup("Chess Club", "new.student@mergington.edu")
        )

        reopened_storage = ActivityStorage(self.database_path)
        activities = reopened_storage.get_activities()

        self.assertEqual(
            activities["Chess Club"]["participants"],
            ["member@mergington.edu", "new.student@mergington.edu"],
        )

    def test_initialize_does_not_overwrite_existing_data(self):
        self.storage.signup("Chess Club", "new.student@mergington.edu")

        self.storage.initialize(SEED_ACTIVITIES)

        self.assertIn(
            "new.student@mergington.edu",
            self.storage.get_activities()["Chess Club"]["participants"],
        )

    def test_duplicate_enrollment_is_rejected(self):
        self.assertFalse(
            self.storage.signup("Chess Club", "member@mergington.edu")
        )

    def test_unregister_removes_persisted_enrollment(self):
        self.assertTrue(
            self.storage.unregister("Chess Club", "member@mergington.edu")
        )
        self.assertNotIn(
            "member@mergington.edu",
            self.storage.get_activities()["Chess Club"]["participants"],
        )


if __name__ == "__main__":
    unittest.main()