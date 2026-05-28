"""
Fetch SBI TT BUY / TT SELL daily reference rates and write clean CSVs.

Source: the sbi-fx-ratekeeper public mirror, which republishes the SBI TT
rates verbatim with full daily history (officialforexrates.com / sbi.co.in
only expose one day at a time, so they cannot be scraped historically).

Every call to refresh() downloads the full upstream file, so any days
missed while this program wasn't running are automatically filled in.
"""

import io
import datetime as dt
from pathlib import Path

import pandas as pd
import requests

CURRENCIES = ["USD", "EUR", "JPY", "GBP"]

UPSTREAM_URL = (
    "https://raw.githubusercontent.com/sahilgupta/"
    "sbi-fx-ratekeeper/main/csv_files/SBI_REFERENCE_RATES_{}.csv"
)

DATA_DIR = Path(__file__).parent / "data"


def _clean(raw_csv_text, currency):
    df = pd.read_csv(io.StringIO(raw_csv_text))
    df = df.rename(columns={"DATE": "date", "TT BUY": "tt_buy", "TT SELL": "tt_sell"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[["date", "tt_buy", "tt_sell"]].dropna()
    df = df[(df["tt_buy"] > 0) & (df["tt_sell"] > 0)]
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.insert(1, "currency", currency)
    return df.sort_values("date").reset_index(drop=True)


def refresh(currency):
    """Download + clean + save one currency. Returns the output path."""
    DATA_DIR.mkdir(exist_ok=True)
    text = requests.get(UPSTREAM_URL.format(currency), timeout=30).text
    df = _clean(text, currency)
    path = DATA_DIR / f"{currency.lower()}.csv"
    df.to_csv(path, index=False)
    return path, len(df), df["date"].iloc[-1]


def refresh_all():
    return {cur: refresh(cur) for cur in CURRENCIES}


def combined_csv():
    """Concatenate all per-currency files into one long-format CSV string."""
    frames = []
    for cur in CURRENCIES:
        path = DATA_DIR / f"{cur.lower()}.csv"
        if path.exists():
            frames.append(pd.read_csv(path))
    if not frames:
        return "date,currency,tt_buy,tt_sell\n"
    out = pd.concat(frames, ignore_index=True).sort_values(["date", "currency"])
    return out.to_csv(index=False)


if __name__ == "__main__":
    for cur, (path, n, latest) in refresh_all().items():
        print(f"{cur}: wrote {n} rows to {path}, latest = {latest}")
