# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It is written to be self-contained: a fresh clone on a new machine plus this file should be enough to pick the project back up.

## Purpose

Publish daily SBI TT BUY / TT SELL reference rates (USD, EUR, JPY, GBP) as raw CSV files in this Git repo, served via `raw.githubusercontent.com` URLs for Excel / Google Sheets ingestion. The repo is intentionally **infrastructure-free**: GitHub Actions does the cron, and the repo itself is the publishing surface.

## Repo identity

| Thing | Value |
|---|---|
| GitHub repo | `c-harsha/sbi-tt` (public, so raw URLs work without auth) |
| Remote (SSH) | `git@github.com:c-harsha/sbi-tt.git` |
| Default branch | `main` (only branch) |
| Local folder name on the old machine | `~/sbi-tt-avg` (left over from the averaging era; the name does not matter) |
| Project name in README | `sbi-tt-rates` |
| Current version | v0.4.1 (see README changelog) |

## Moving to a new machine

### 1. Prerequisites

- **Git** with an SSH key added to the `c-harsha` GitHub account. Test with `ssh -T git@github.com`. Or clone over HTTPS instead.
- **Python 3.12+**. CI uses 3.12; the old machine ran 3.13.5. Both work.
- **GitHub CLI (`gh`)**, optional but handy for checking and triggering workflow runs. Run `gh auth login` and choose SSH as the git protocol.

### 2. Clone and set up

```bash
git clone git@github.com:c-harsha/sbi-tt.git
cd sbi-tt
python3 -m venv venv              # venv/ is gitignored
./venv/bin/pip install -r requirements.txt
./venv/bin/python fetcher.py      # optional: regenerates data/ locally
```

`fetcher.py` should print four lines like `USD: wrote 1626 rows to .../data/usd.csv, latest = 2026-11-02`.

### 3. What does NOT come with `git clone`

| Item | Where it lived on the old machine | What to do |
|---|---|---|
| `venv/` | `./venv` | Recreate as above. |
| Claude Code permissions | `.claude/settings.local.json`, ignored via the global `~/.config/git/ignore` | Optional. Most old entries were stale (Streamlit, Docker, Flask, an unrelated project). The ones still useful: `Bash(python fetcher.py)`, `Bash(./venv/bin/python *)`, `Bash(pip install *)`, `Bash(./venv/bin/pip install *)`, `Bash(gh workflow *)`, `Bash(gh run *)`, `Bash(git add *)`, `Bash(git push *)`. |
| Claude Code memory | `~/.claude/projects/-home-harsha-sbi-tt-avg/memory/` | Was empty. Nothing to copy. |
| `gh` auth, SSH keys | `~/.config/gh/`, `~/.ssh/` | Set up fresh on the new machine. Don't copy tokens around. |

Nothing else is machine-specific. No secrets, no `.env`, no local services.

### 4. Always pull before editing

The bot commits to `main` almost every day (`data: refresh YYYY-MM-DD`). A local checkout falls behind quickly: the old machine was 114 commits behind by 2026-11-03. Before changing anything:

```bash
git pull --rebase
```

Upstream bot commits only ever touch `data/`, so rebasing code changes on top of them won't conflict unless you also edited `data/` by hand. Don't do that; let the workflow regenerate it.

## State as of 2026-11-03

- Workflow is healthy: every scheduled run in late Oct / early Nov 2026 succeeded in about 20 seconds.
- Latest published row: `2026-11-02` (USD 94.50 / 95.35).
- Row counts: USD, EUR and GBP have 1626 rows each; JPY has 1625 (one upstream zero row dropped).
- No code changes since the initial commit `6ef1bc6`. Apart from the v0.4.1 docs update (README changelog and this file), every later commit is a bot data refresh.

## Files

```
.
├── fetcher.py                     # download + clean + write data/*.csv
├── requirements.txt               # pandas, requests (unpinned)
├── .github/workflows/refresh.yml  # daily cron + commit-back
├── data/
│   ├── usd.csv
│   ├── eur.csv
│   ├── jpy.csv
│   └── gbp.csv
├── README.md                      # user-facing: URLs, Sheets/Excel usage, changelog
├── CLAUDE.md                      # this file
└── .gitignore                     # __pycache__/, *.pyc, venv/, .streamlit/
```

`.streamlit/` in `.gitignore` is a leftover from v0.2.0 and harmless.

## `fetcher.py`

- `CURRENCIES = ["USD", "EUR", "JPY", "GBP"]`: the only list to edit when adding or removing a currency.
- `UPSTREAM_URL`: format string for the sbi-fx-ratekeeper raw CSVs.
- `_clean(raw_csv_text, currency)`:
  - renames upstream `DATE` / `TT BUY` / `TT SELL` to `date` / `tt_buy` / `tt_sell`
  - parses dates with `errors="coerce"` and drops unparseable rows and NaNs
  - drops rows where either rate is `<= 0` (early upstream rows stored as `0`)
  - formats dates as ISO `YYYY-MM-DD`, inserts a `currency` column, sorts by date
- `refresh(currency)`: fetches with a 30 s timeout, cleans, and writes `data/<code>.csv`. Returns `(path, row_count, latest_date)`.
- `refresh_all()`: calls `refresh` for every currency.
- `combined_csv()`: **unused**. Left over from the v0.3.0 Flask `/all.csv` endpoint. Safe to delete, or reuse if a combined `data/all.csv` is ever wanted.

Behaviour to preserve:

- **Idempotent, full-history rewrite.** Every run downloads the whole upstream history and rewrites each file from scratch. That means there's no incremental state, and any missed days backfill on the next successful run. Don't add "append only new rows" logic.
- **No HTTP status check.** `requests.get(...).text` is used directly. If upstream ever returns an error page, `_clean` will probably raise (missing columns) and the workflow fails loudly, which is the desired outcome. Keep it failing loudly rather than writing an empty CSV.

## Output CSV contract (don't break it)

Spreadsheets point at these URLs. Changing column names, order, date format or file paths breaks every consumer silently.

```
date,currency,tt_buy,tt_sell
2020-01-06,USD,71.65,72.5
```

- Columns, in this order: `date, currency, tt_buy, tt_sell`
- `date` is ISO `YYYY-MM-DD`
- `currency` is the uppercase code; file names are lowercase (`usd.csv`)
- Rates are as published, with no rounding (pandas drops trailing zeros, e.g. `72.5`)
- One file per currency under `data/`

Public URLs:

```
https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/usd.csv
https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/eur.csv
https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/jpy.csv
https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/gbp.csv
```

Renaming the repo, renaming the branch or making the repo private would break these URLs.

## Workflow (`.github/workflows/refresh.yml`)

- Triggers: `schedule` (`30 13 * * *` = 13:30 UTC = 19:00 IST), `push` to `main`, and `workflow_dispatch`. The push trigger means code changes regenerate `data/` immediately.
- In practice GitHub delays scheduled runs heavily: recent runs started between about 17:50 and 22:30 UTC. That's fine because the data is only needed by the next morning. Don't "fix" it by adding more cron entries.
- Steps: checkout → `setup-python@v5` (3.12, pip cache) → `pip install -r requirements.txt` → `python fetcher.py` → commit and push `data/` only if `git status --porcelain data/` is non-empty.
- Auth: the default `GITHUB_TOKEN` with `permissions: contents: write`. There are no secrets to manage.
- Commit author: `github-actions[bot]` (`41898282+github-actions[bot]@users.noreply.github.com`). Message: `data: refresh <UTC date>`.
- `concurrency: refresh-rates` with `cancel-in-progress: true` keeps runs from piling up.
- Bot pushes made with `GITHUB_TOKEN` don't re-trigger the `push` workflow (GitHub's built-in loop protection), so there's no infinite loop.
- GitHub auto-disables scheduled workflows after 60 days with no repo activity. The daily bot commits count as activity, so this shouldn't happen. If the data ever stops updating, check the Actions tab for a "disabled" banner first.

## Common tasks

```bash
# Run locally
./venv/bin/python fetcher.py

# Check recent workflow runs
gh run list --limit 10

# See logs of a failed run
gh run view <run-id> --log-failed

# Trigger a refresh manually
gh workflow run refresh-rates

# Peek at the latest published values without pulling
git fetch && git show origin/main:data/usd.csv | tail -3
```

**Add a currency:** append its code to `CURRENCIES` in `fetcher.py`, check that `SBI_REFERENCE_RATES_<CODE>.csv` exists upstream, then commit and push. The push trigger produces `data/<code>.csv` within a minute. Add its URL to README's table too.

**Remove a currency:** remove it from `CURRENCIES` **and** `git rm data/<code>.csv`. The fetcher never deletes files.

**Record a change:** for any code or docs change, add an entry at the top of the README changelog, move the `— current` label onto it, and bump the version in the Repo identity table above. Bot data refreshes don't get changelog entries.

## Data source

`sahilgupta/sbi-fx-ratekeeper` on GitHub is a public daily mirror of SBI TT rates going back to 2020-01-06. SBI's own pages serve only one day at a time via JavaScript, so they can't supply historical data in bulk. The mirror reproduces SBI's values verbatim.

```
https://raw.githubusercontent.com/sahilgupta/sbi-fx-ratekeeper/main/csv_files/SBI_REFERENCE_RATES_{USD|EUR|JPY|GBP}.csv
```

This is a single third-party dependency. If it stops updating, our CSVs stop updating too: the workflow still succeeds, it just reports "No changes." Symptom: the latest date in `data/usd.csv` is more than 3 to 4 days old outside a holiday stretch. There's no automatic alert for this.

## Domain notes

- TT BUY and TT SELL are tracked independently. Never collapse them to a mid rate.
- JPY is quoted **per 100 yen**, matching SBI. Don't rescale.
- SBI publishes on Indian banking days, which **include the 1st, 3rd and 5th Saturdays** of each month (2nd and 4th Saturdays are bank holidays). Sundays and bank holidays are skipped, and the CSV simply has no row for those dates. Don't fill gaps.
- Known upstream oddity: all four currencies have a row for **Sunday 2026-09-27**. It is passed through as-is. Don't special-case it unless upstream corrects it.
- Some early upstream rows are stored as `0`, and `_clean` drops them. That's why JPY has one row fewer than the others.

## Dependencies

`requirements.txt` is unpinned (`pandas`, `requests`). Versions on the old machine were pandas 3.0.3, numpy 2.4.6 and requests 2.34.2. CI installs the latest on every run. If a future pandas release breaks `_clean`, pin the last good version in `requirements.txt`.

## Tests

None. To verify a change, run `fetcher.py` locally and run `git diff --stat data/`. A code-only change (no intended data change) should produce an empty diff.

## Deliberately out of scope

Averaging, charting, Excel export, email delivery, web UI, self-hosted serving and containerisation. All of these existed in v0.1.0 to v0.3.0 (`sbi_forex.py`, Streamlit app, Flask `server.py`, Dockerfile, docker-compose, GitLab CI). That code is **not** in this repo's git history: the repo was re-initialised at v0.4.0 with a single initial commit. The README changelog is the only record. Any of those features would have to be rebuilt from scratch, and doing so would contradict the project's infrastructure-free goal.
