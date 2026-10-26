"""Refresh stock listings without deleting portfolio-linked records."""

import csv
import io
import httpx
from config import get_settings
from init_db import STOCK_LIST_FILE, seed_stock_catalog


def download_csv():
    key = get_settings().ALPHA_VANTAGE_API_KEY
    if not key:
        raise ValueError(
            "Set ALPHA_VANTAGE_API_KEY before refreshing the stock catalog"
        )
    response = httpx.get(
        "https://www.alphavantage.co/query",
        params={"function": "LISTING_STATUS", "apikey": key},
        timeout=30,
    )
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.text.lstrip("\ufeff")))
    if not {"symbol", "name", "status"}.issubset(reader.fieldnames or []):
        raise ValueError(
            "Provider did not return a stock listing CSV; the existing file was preserved"
        )
    rows = list(reader)
    if not any(
        row.get("status", "").strip().lower() == "active"
        and row.get("symbol", "").strip()
        and row.get("name", "").strip()
        for row in rows
    ):
        raise ValueError("No active stocks returned; the existing file was preserved")
    temporary = STOCK_LIST_FILE.with_suffix(".csv.tmp")
    temporary.write_text(response.text, encoding="utf-8")
    temporary.replace(STOCK_LIST_FILE)
    return STOCK_LIST_FILE


def import_csvfile_to_db():
    seed_stock_catalog()


if __name__ == "__main__":
    download_csv()
    import_csvfile_to_db()
