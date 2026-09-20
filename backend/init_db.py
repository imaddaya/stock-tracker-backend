import csv
from pathlib import Path

from sqlalchemy import text

from database import Base, SessionLocal, engine
from models import StocksTable
from utils.crypto import encrypt_secret, is_encrypted_secret


BASE_DIR = Path(__file__).resolve().parent
STOCK_LIST_FILE = BASE_DIR / "listing_status.csv"


def create_schema() -> None:
    print("Initializing database schema...")

    Base.metadata.create_all(bind=engine)

    print("Database schema is ready.")


def encrypt_existing_user_api_keys() -> None:
    print("Checking stored Alpha Vantage API key encryption...")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE users_table
                ALTER COLUMN alpha_vantage_api_key TYPE TEXT
                """
            )
        )

        rows = connection.execute(
            text(
                """
                SELECT id, alpha_vantage_api_key
                FROM users_table
                """
            )
        ).mappings().all()

        migrated = 0

        for row in rows:
            stored_key = row["alpha_vantage_api_key"]

            if not stored_key or is_encrypted_secret(stored_key):
                continue

            connection.execute(
                text(
                    """
                    UPDATE users_table
                    SET alpha_vantage_api_key = :encrypted_key
                    WHERE id = :user_id
                    """
                ),
                {
                    "encrypted_key": encrypt_secret(stored_key),
                    "user_id": row["id"],
                },
            )

            migrated += 1

    print(
        "API key encryption is ready: "
        f"{migrated} existing key(s) encrypted."
    )


def enforce_user_stock_uniqueness() -> None:
    print(
        "Checking portfolio and stock cache "
        "uniqueness..."
    )

    with engine.begin() as connection:
        portfolio_result = connection.execute(
            text(
                """
                DELETE FROM portfolios_table AS duplicate
                USING portfolios_table AS keeper
                WHERE duplicate.user_id = keeper.user_id
                  AND duplicate.stock_symbol = keeper.stock_symbol
                  AND duplicate.id > keeper.id
                """
            )
        )

        cache_result = connection.execute(
            text(
                """
                DELETE FROM stock_data_cache AS older
                USING stock_data_cache AS newer
                WHERE older.user_id = newer.user_id
                  AND older.stock_symbol = newer.stock_symbol
                  AND (
                      older.last_updated < newer.last_updated
                      OR (
                          older.last_updated = newer.last_updated
                          AND older.id < newer.id
                      )
                  )
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname =
                            'uq_portfolios_user_stock'
                          AND conrelid =
                            'portfolios_table'::regclass
                    ) THEN
                        ALTER TABLE portfolios_table
                        ADD CONSTRAINT
                            uq_portfolios_user_stock
                        UNIQUE (
                            user_id,
                            stock_symbol
                        );
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname =
                            'uq_stock_data_cache_user_stock'
                          AND conrelid =
                            'stock_data_cache'::regclass
                    ) THEN
                        ALTER TABLE stock_data_cache
                        ADD CONSTRAINT
                            uq_stock_data_cache_user_stock
                        UNIQUE (
                            user_id,
                            stock_symbol
                        );
                    END IF;
                END
                $$;
                """
            )
        )

    portfolio_removed = max(
        portfolio_result.rowcount or 0,
        0,
    )

    cache_removed = max(
        cache_result.rowcount or 0,
        0,
    )

    print(
        "User/stock uniqueness is ready: "
        f"{portfolio_removed} duplicate portfolio row(s) removed, "
        f"{cache_removed} duplicate cache row(s) removed."
    )


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

        required_columns = {
            "symbol",
            "name",
            "status",
        }

        available_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns
            - available_columns
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "listing_status.csv is missing "
                f"required columns: {missing}"
            )

        for row in reader:
            if (
                row["status"]
                .strip()
                .lower()
                != "active"
            ):
                continue

            symbol = (
                row["symbol"]
                .strip()
                .upper()
            )

            company_name = (
                row["name"]
                .strip()
            )

            if not symbol or not company_name:
                continue

            stocks[symbol] = company_name

    if not stocks:
        raise ValueError(
            "listing_status.csv did not contain "
            "any active stock listings."
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
            existing_row = existing.get(
                symbol
            )

            if existing_row is None:
                rows_to_insert.append(
                    {
                        "stock_symbol": symbol,
                        "stock_company_name": (
                            company_name
                        ),
                        "is_listed": True,
                    }
                )

                continue

            if (
                existing_row.stock_company_name
                != company_name
                or existing_row.is_listed
                is not True
            ):
                rows_to_update.append(
                    {
                        "stock_symbol": symbol,
                        "stock_company_name": (
                            company_name
                        ),
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
    encrypt_existing_user_api_keys()
    enforce_user_stock_uniqueness()
    seed_stock_catalog()


if __name__ == "__main__":
    init_database()