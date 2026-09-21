import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_acnc_register import archive_name, parse_ckan_datetime, should_download


class FetchTests(unittest.TestCase):
    def test_first_run_downloads(self):
        current = datetime(2026, 9, 20, 19, tzinfo=timezone.utc)
        self.assertTrue(should_download(current, None))

    def test_requires_full_seven_day_advance(self):
        previous = datetime(2026, 9, 13, 20, tzinfo=timezone.utc)
        self.assertFalse(
            should_download(datetime(2026, 9, 20, 19, 59, 59, tzinfo=timezone.utc), previous)
        )
        self.assertTrue(
            should_download(datetime(2026, 9, 20, 20, tzinfo=timezone.utc), previous)
        )

    def test_archive_uses_sydney_source_date(self):
        update = parse_ckan_datetime("2026-09-20T19:00:20.049365")
        self.assertEqual(archive_name(update), "datadotgov_main-20260921.csv")


if __name__ == "__main__":
    unittest.main()
