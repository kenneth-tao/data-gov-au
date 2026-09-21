#!/usr/bin/env python3
"""Archive weekly versions of the data.gov.au ACNC register CSV."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PACKAGE_ID = "b050b242-4487-4306-abf5-07ca073e5594"
RESOURCE_ID = "8fb32972-24e9-4c95-885e-7140be51be8a"
API_URL = f"https://data.gov.au/data/api/3/action/package_show?id={PACKAGE_ID}"
DATA_DIR = Path("data/acnc-register-of-australian-charities")
STATE_FILE = DATA_DIR / ".resource-state.json"
ARCHIVE_PREFIX = "datadotgov_main-"
MAX_VERSIONS = 4
MIN_UPDATE_AGE = timedelta(days=7)
SYDNEY = ZoneInfo("Australia/Sydney")
USER_AGENT = "data-gov-au-archiver/1.0 (+https://github.com/)"


def parse_ckan_datetime(value: str) -> datetime:
    """Parse a CKAN timestamp and return an aware UTC datetime."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def should_download(current: datetime, previous: datetime | None) -> bool:
    """Download on first run, then only after the resource date advances 7 days."""
    return previous is None or current - previous >= MIN_UPDATE_AGE


def sydney_date(moment: datetime) -> str:
    return moment.astimezone(SYDNEY).date().isoformat()


def completed_today(state: dict[str, Any], now: datetime) -> bool:
    """Return whether an archive was already downloaded today in Sydney."""
    return state.get("successful_run_date_sydney") == sydney_date(now)


def request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def find_resource(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("success"):
        raise RuntimeError("The data.gov.au CKAN API returned success=false")
    for resource in payload["result"]["resources"]:
        if resource.get("id") == RESOURCE_ID:
            return resource
    raise RuntimeError(f"Resource {RESOURCE_ID} was not present in package metadata")


def read_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def archive_name(last_modified: datetime) -> str:
    local_date = last_modified.astimezone(SYDNEY).strftime("%Y%m%d")
    return f"{ARCHIVE_PREFIX}{local_date}.csv"


def download_csv(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            content_type = response.headers.get_content_type()
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, delete=False
            ) as temporary:
                temp_name = temporary.name
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)

        temporary_path = Path(temp_name)
        if temporary_path.stat().st_size == 0:
            raise RuntimeError("Downloaded CSV is empty")
        with temporary_path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle), [])
        if "ABN" not in header or "Charity_Legal_Name" not in header:
            raise RuntimeError(
                f"Downloaded content does not look like the ACNC CSV ({content_type})"
            )
        os.replace(temporary_path, destination)
        temp_name = None
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)


def remove_old_versions() -> list[Path]:
    archives = sorted(DATA_DIR.glob(f"{ARCHIVE_PREFIX}[0-9]*.csv"), reverse=True)
    removed = archives[MAX_VERSIONS:]
    for path in removed:
        path.unlink()
    return removed


def write_state(resource: dict[str, Any], archive: Path, now: datetime) -> None:
    state = {
        "resource_id": RESOURCE_ID,
        "source_last_modified": resource["last_modified"],
        "source_url": resource["url"],
        "archive_file": archive.name,
        "fetched_at_utc": now.isoformat(),
        "successful_run_date_sydney": sydney_date(now),
    }
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    state = read_state()
    if completed_today(state, now):
        print(f"No action needed: an archive was already downloaded on {sydney_date(now)}.")
        return 0

    resource = find_resource(request_json(API_URL))
    if not resource.get("last_modified") or not resource.get("url"):
        raise RuntimeError("Resource metadata is missing last_modified or url")

    current_update = parse_ckan_datetime(resource["last_modified"])
    previous_update = (
        parse_ckan_datetime(state["source_last_modified"])
        if state.get("source_last_modified")
        else None
    )
    if not should_download(current_update, previous_update):
        elapsed = current_update - previous_update  # type: ignore[operator]
        print(
            "No archive created yet: source update advanced by "
            f"{elapsed.days} days, less than the required 7 days. "
            "The next scheduled hourly run will try again."
        )
        return 0

    destination = DATA_DIR / archive_name(current_update)
    download_csv(resource["url"], destination)
    removed = remove_old_versions()
    write_state(resource, destination, now)

    print(f"Archived {destination} ({destination.stat().st_size:,} bytes)")
    for path in removed:
        print(f"Removed old archive {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
