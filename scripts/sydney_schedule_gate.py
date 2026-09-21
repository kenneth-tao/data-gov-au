#!/usr/bin/env python3
"""Select the UTC cron that corresponds to 09:00 Australia/Sydney."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def should_run(event_name: str, schedule: str, now: datetime | None = None) -> bool:
    if event_name == "workflow_dispatch":
        return True
    now = now or datetime.now(timezone.utc)
    offset_hours = int(now.astimezone(ZoneInfo("Australia/Sydney")).utcoffset().total_seconds() // 3600)
    expected_schedule = "0 22 * * 0" if offset_hours == 11 else "0 23 * * 0"
    return schedule == expected_schedule


def main() -> None:
    run = should_run(
        os.environ.get("GITHUB_EVENT_NAME", ""),
        os.environ.get("GITHUB_EVENT_SCHEDULE", ""),
    )
    output = Path(os.environ["GITHUB_OUTPUT"])
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"run={'true' if run else 'false'}\n")
    print("Running this invocation." if run else "Skipping the inactive Sydney UTC schedule.")


if __name__ == "__main__":
    main()
