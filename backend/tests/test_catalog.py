from unittest.mock import Mock
import pytest
import import_stocks
import init_db
from models import PortfoliosTable, StocksTable


def test_catalog_refresh_preserves_portfolios_and_updates_existing_stocks(
    db, make_user, tmp_path, monkeypatch
):
    user, _ = make_user()
    db.add(
        StocksTable(stock_symbol="AAPL", stock_company_name="Old name", is_listed=True)
    )
    db.flush()
    db.add(PortfoliosTable(user_id=user.id, stock_symbol="AAPL"))
    db.commit()
    listing = tmp_path / "listing_status.csv"
    listing.write_text(
        "symbol,name,status\nAAPL,Apple Inc,Active\nMSFT,Microsoft,Active\n"
    )
    monkeypatch.setattr(init_db, "STOCK_LIST_FILE", listing)
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(init_db, "SessionLocal", sessionmaker(bind=db.get_bind()))
    import_stocks.import_csvfile_to_db()
    import_stocks.import_csvfile_to_db()
    db.expire_all()
    assert db.get(StocksTable, "AAPL").stock_company_name == "Apple Inc"
    assert db.query(StocksTable).count() == 2
    assert db.query(PortfoliosTable).filter_by(user_id=user.id).count() == 1


@pytest.mark.parametrize(
    "body", ['{"Information":"rate limit"}', "symbol,name,status\n"]
)
def test_failed_provider_response_preserves_existing_catalog(
    tmp_path, monkeypatch, body
):
    listing = tmp_path / "listing_status.csv"
    listing.write_text("original listing")
    monkeypatch.setattr(import_stocks, "STOCK_LIST_FILE", listing)
    monkeypatch.setattr(
        import_stocks,
        "get_settings",
        lambda: Mock(ALPHA_VANTAGE_API_KEY="fake-test-key"),
    )
    monkeypatch.setattr(import_stocks.httpx, "get", lambda *_a, **_k: Mock(text=body))
    with pytest.raises(ValueError):
        import_stocks.download_csv()
    assert listing.read_text() == "original listing"
