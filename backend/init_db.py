import csv
from pathlib import Path

from database import Base, SessionLocal, engine
from models import StocksTable


BASE_DIR = Path(__file__).resolve().parent
STOCK_LIST_FILE = BASE_DIR / "listing_status.csv"


def create_schema() -> None:
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("Database schema is ready.")


def load_stock_catalog() -> dict[str, str]:
    if not STOCK_LIST_FILE.exists():
        raise FileNotFoundError(
            f"Stock listing file not found: {STOCK_LIST_FILE}"
        )

    stocks: dict[str, str] = {}

    with STOCK_LIST_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csvfile:
        reader = csv.DictReader(csvfile)

        required_columns = {"symbol", "name", "status"}
        available_columns = set(reader.fieldnames or [])

        missing_columns = required_columns - available_columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(
                f"listing_status.csv is missing required columns: {missing}"
            )

        for row in reader:
            if row["status"].strip().lower() != "active":
                continue

            symbol = row["symbol"].strip().upper()
            company_name = row["name"].strip()

            if not symbol or not company_name:
                continue

            stocks[symbol] = company_name

    if not stocks:
        raise ValueError(
            "listing_status.csv did not contain any active stock listings."
        )

    return stocks


def seed_stock_catalog() -> None:
    catalog = load_stock_catalog()
    db = SessionLocal()

    try:
        existing_rows = db.query(
            StocksTable.stock_symbol,
            StocksTable.stock_company_name,
            StocksTable.is_listed,
        ).all()

        existing = {
            row.stock_symbol: row
            for row in existing_rows
        }

        rows_to_insert = []
        rows_to_update = []

        for symbol, company_name in catalog.items():
            existing_row = existing.get(symbol)

            if existing_row is None:
                rows_to_insert.append(
                    {
                        "stock_symbol": symbol,
                        "stock_company_name": company_name,
                        "is_listed": True,
                    }
                )
                continue

            if (
                existing_row.stock_company_name != company_name
                or existing_row.is_listed is not True
            ):
                rows_to_update.append(
                    {
                        "stock_symbol": symbol,
                        "stock_company_name": company_name,
                        "is_listed": True,
                    }
                )

        if rows_to_insert:
            db.bulk_insert_mappings(
                StocksTable,
                rows_to_insert,
            )

        if rows_to_update:
            db.bulk_update_mappings(
                StocksTable,
                rows_to_update,
            )

        db.commit()

        print(
            "Stock catalog is ready: "
            f"{len(catalog)} active listings, "
            f"{len(rows_to_insert)} inserted, "
            f"{len(rows_to_update)} updated."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def init_database() -> None:
    create_schema()
    seed_stock_catalog()


if __name__ == "__main__":
    init_database()