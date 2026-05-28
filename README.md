# sbi-tt-rates

Daily-refreshed CSV files of the **SBI TT BUY / TT SELL** reference rates for **USD, EUR, JPY, GBP**, published as raw files in this Git repo. Designed for direct ingestion by Excel ("Data → From Web") and Google Sheets (`=IMPORTDATA`). No analysis layer — you do that in your spreadsheet.

## URLs

Point your spreadsheet at the raw file on GitHub. Replace `c-harsha/sbi-tt` with this repo's path.

| Currency | URL |
|---|---|
| USD | `https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/usd.csv` |
| EUR | `https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/eur.csv` |
| JPY | `https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/jpy.csv` |
| GBP | `https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/gbp.csv` |

CSV columns: `date, currency, tt_buy, tt_sell`. Dates are `YYYY-MM-DD`. JPY is quoted **per 100 yen**, matching SBI's convention.

### Google Sheets

```
=IMPORTDATA("https://raw.githubusercontent.com/c-harsha/sbi-tt/main/data/usd.csv")
```

### Excel

`Data → From Web →` paste the URL.

## How it works

- **`fetcher.py`** — downloads the upstream SBI TT history, cleans it (rename columns, drop zero-valued rows, ISO date format), writes one CSV per currency to `data/`.
- **`.github/workflows/refresh.yml`** — runs `fetcher.py` daily at 13:30 UTC (19:00 IST) and on every push to `main`. If any CSV changed, it commits and pushes the new files back to this repo. Manual triggers are available from the Actions tab.

Because the upstream file always carries the full history, a successful refresh automatically backfills any days that were missed (e.g. during an Actions outage). No special catch-up logic needed.

## Data source

Upstream: `sahilgupta/sbi-fx-ratekeeper` on GitHub — a public daily mirror of SBI TT rates, since 6 January 2020. SBI's own pages only render one day at a time via JavaScript, so they cannot supply historical bulk. The mirror reproduces SBI's published values verbatim.

Data coverage: every working day from **2020-01-06** onward. No data exists upstream before then.

## Run locally (optional)

```bash
pip install -r requirements.txt
python fetcher.py
ls data/
```

## Changelog

### v0.4.0 — current
- Switched the publishing surface from a self-hosted Flask server to **GitHub Pages-style raw URLs** backed by a daily GitHub Actions workflow.
- Removed: Flask server, Dockerfile, docker-compose, GitLab CI pipeline, in-container scheduler. The repo no longer needs any infrastructure.

### v0.3.0
- Project pivoted from averages to raw CSV publishing.
- Added Flask server publishing `/usd.csv`, `/eur.csv`, `/jpy.csv`, `/gbp.csv`, `/all.csv`.
- Multi-arch (linux/amd64 + linux/arm64) Docker image; GitLab CI build/test/publish pipeline.
- Docker Compose example.

### v0.2.0
- Streamlit web UI with time-frame selector, per-currency tabs, latest-rate panel, Excel download.
- Local CSV cache + daily scheduler.

### v0.1.0
- Initial CLI in `sbi_forex.py`: calendar-aligned weekly / monthly / quarterly / yearly averages, styled Excel export, optional Gmail SMTP delivery.
