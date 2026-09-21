import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sydney_schedule_gate import should_run


class ScheduleGateTests(unittest.TestCase):
    def test_manual_runs_always_continue(self):
        self.assertTrue(should_run("workflow_dispatch", ""))

    def test_daylight_saving_uses_2200_utc(self):
        summer = datetime(2026, 1, 4, 22, tzinfo=timezone.utc)
        self.assertTrue(should_run("schedule", "0 22 * * 0", summer))
        self.assertFalse(should_run("schedule", "0 23 * * 0", summer))

    def test_standard_time_uses_2300_utc(self):
        winter = datetime(2026, 7, 5, 23, tzinfo=timezone.utc)
        self.assertTrue(should_run("schedule", "0 23 * * 0", winter))
        self.assertFalse(should_run("schedule", "0 22 * * 0", winter))


if __name__ == "__main__":
    unittest.main()
