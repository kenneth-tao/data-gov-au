# data-gov-au

An automated archive of the [ACNC Register of Australian charities CSV](https://data.gov.au/data/dataset/acnc-register/resource/8fb32972-24e9-4c95-885e-7140be51be8a).

## Schedule and behaviour

The GitHub Actions workflow uses timezone-aware scheduling to run each Monday at 09:00 Australia/Sydney time, including across daylight-saving changes. The workflow can also be run manually.

On each eligible run it:

1. Reads the resource's `last_modified` value from the data.gov.au CKAN API.
2. Continues only when that value is at least seven days newer than the value archived on the previous successful run.
3. Downloads and validates the CSV.
4. Stores it in `data/acnc-register-of-australian-charaties/` as `datadotgov_main-YYYYMMDD.csv`, using the resource update date in Sydney.
5. Retains the newest four CSV versions and commits any changes.

The state file in the data directory records the source timestamp used by the next run.

## Run locally

Python 3.9 or newer is required. No third-party packages are used.

```sh
python3 scripts/fetch_acnc_register.py
python3 -m unittest discover -s tests -v
```

## Source and licence

The source dataset is published by the Australian Charities and Not-for-profits Commission on data.gov.au under the [Creative Commons Attribution 3.0 Australia licence](https://creativecommons.org/licenses/by/3.0/au/). See the source page for full metadata and attribution information.
