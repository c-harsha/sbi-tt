# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Publish daily SBI TT BUY / TT SELL reference rates (USD, EUR, JPY, GBP) as raw CSV files in this Git repo, served via `raw.githubusercontent.com` URLs for Excel / Google Sheets ingestion. The repo is intentionally **infrastructure-free** — GitHub Actions does the cron, the repo itself is the publishing surface.

## Status

Two-file project:

- **`fetcher.py`** — downloads the full upstream history, cleans it, writes `data/<currency>.csv`. Idempotent.
- **`.github/workflows/refresh.yml`** — daily cron (13:30 UTC = 19:00 IST), runs `fetcher.py`, commits any changed CSVs back to `main`.

No server, no Docker, no scheduler process. Everything else from earlier versions (Flask, Streamlit, averaging, Excel export, email, GitLab CI, multi-arch images) has been removed.

## Run / build / test

```bash
pip install -r requirements.txt    # pandas, requests
python fetcher.py                  # populates data/
```

No tests.

## Workflow notes

- The workflow runs on `schedule`, `push: main`, and `workflow_dispatch`. Push triggers exist so code changes regenerate `data/` immediately.
- The job uses the default `GITHUB_TOKEN` with `contents: write` to commit back. No secrets to manage.
- `concurrency.cancel-in-progress: true` prevents queue pile-up.
- Commit author is `github-actions[bot]`.

## Data source

`sahilgupta/sbi-fx-ratekeeper` on GitHub — public daily mirror of SBI TT rates since 2020-01-06. SBI's own pages serve only one day at a time via JavaScript, so they cannot supply historical bulk. The mirror reproduces SBI's values verbatim.

```
https://raw.githubusercontent.com/sahilgupta/sbi-fx-ratekeeper/main/csv_files/SBI_REFERENCE_RATES_{USD|EUR|JPY|GBP}.csv
```

## Domain notes

- TT BUY and TT SELL are tracked independently — never collapse to a mid rate.
- JPY is quoted per 100 yen, matching SBI. Do not re-scale.
- SBI does not publish on weekends/Indian bank holidays. CSV simply skips those dates.
- Some early upstream rows are stored as `0` — `fetcher._clean` drops them.
- Adding a currency = appending its code to `CURRENCIES` in `fetcher.py`; GitHub Pages/raw URL appears automatically once the next refresh commits the file.

## Deliberately out of scope

Averaging, charting, Excel export, email delivery, web UI, self-hosted serving, containerisation. Pre-v0.4.0 git history has all of these if reference is needed.
