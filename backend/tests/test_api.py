from datetime import date

import bcrypt
import pytest

from models import (
    EmailReminderDelivery,
    PortfoliosTable,
    StockDataCache,
    StocksTable,
    UsersTable,
)
from utils.jwt import create_account_deletion_token, create_verification_token


@pytest.mark.parametrize(
    "password", ["StrongPass1!" + "x" * 72, "StrongPass1!" + "é" * 40]
)
def test_signup_rejects_passwords_exceeding_bcrypt_byte_limit(client, password):
    response = client.post(
        "/auth/signup",
        json={
            "email": "new@example.com",
            "password": password,
            "confirm_password": password,
            "alpha_vantage_api_key": "fake-key",
        },
    )
    assert response.status_code == 422
    assert "72 UTF-8 bytes" in response.text


def test_login_returns_access_token(client, make_user):
    user, _ = make_user()
    response = client.post(
        "/auth/login", json={"email": user.email, "password": "StrongPass1!"}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/portfolio/summary", headers=headers).status_code == 200


@pytest.mark.parametrize("password", ["wrong", "", "x" * 73])
def test_invalid_password_rejected(client, make_user, password):
    user, _ = make_user()
    assert (
        client.post(
            "/auth/login", json={"email": user.email, "password": password}
        ).status_code
        == 401
    )


def test_unverified_user_cannot_log_in(client, make_user):
    user, _ = make_user(verified=False)
    assert (
        client.post(
            "/auth/login", json={"email": user.email, "password": "StrongPass1!"}
        ).status_code
        == 403
    )


def test_protected_route_requires_token(client):
    assert client.get("/portfolio/summary").status_code in (401, 403)


def test_verification_token_cannot_be_used_as_access_token(client, make_user):
    user, _ = make_user()
    assert (
        client.get(
            "/portfolio/summary",
            headers={
                "Authorization": f"Bearer {create_verification_token(user.email)}"
            },
        ).status_code
        == 401
    )


def test_password_change_invalidates_access_token(client, make_user, db):
    user, headers = make_user()
    user.hashed_password = bcrypt.hashpw(
        b"NewStrongPass2!", bcrypt.gensalt(rounds=4)
    ).decode()
    db.commit()
    assert client.get("/portfolio/summary", headers=headers).status_code == 401


def seed_portfolio(db, user, price):
    if db.get(StocksTable, "AAPL") is None:
        db.add(
            StocksTable(stock_symbol="AAPL", stock_company_name="Apple", is_listed=True)
        )
        db.flush()
    db.add(PortfoliosTable(user_id=user.id, stock_symbol="AAPL"))
    db.add(StockDataCache(user_id=user.id, stock_symbol="AAPL", current_price=price))
    db.commit()


def test_summary_reads_only_current_users_cache(client, make_user, db):
    owner, headers = make_user()
    other, _ = make_user("other@example.com")
    seed_portfolio(db, owner, 101)
    seed_portfolio(db, other, 999)
    response = client.get("/portfolio/summary", headers=headers)
    assert response.status_code == 200
    assert [(r["symbol"], r["price"]) for r in response.json()] == [("AAPL", 101)]


def test_remove_stock_preserves_other_users_portfolio_and_cache(client, make_user, db):
    owner, headers = make_user()
    other, _ = make_user("other@example.com")
    seed_portfolio(db, owner, 101)
    seed_portfolio(db, other, 999)
    assert client.delete("/portfolio/remove/aapl", headers=headers).status_code == 200
    assert db.query(PortfoliosTable).filter_by(user_id=owner.id).count() == 0
    assert db.query(StockDataCache).filter_by(user_id=owner.id).count() == 0
    assert db.query(PortfoliosTable).filter_by(user_id=other.id).count() == 1
    assert db.query(StockDataCache).filter_by(user_id=other.id).count() == 1


def test_cannot_read_or_remove_another_users_stock(client, make_user, db):
    _, headers = make_user()
    other, _ = make_user("other@example.com")
    seed_portfolio(db, other, 999)
    assert client.delete("/portfolio/remove/AAPL", headers=headers).status_code == 404
    response = client.get("/portfolio/summary/AAPL", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found in your portfolio"


def test_duplicate_portfolio_add_is_rejected(client, make_user, db):
    _, headers = make_user()
    db.add(StocksTable(stock_symbol="AAPL", stock_company_name="Apple"))
    db.commit()
    assert (
        client.post(
            "/portfolio/add", json={"stock_symbol": "aapl"}, headers=headers
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/portfolio/add", json={"stock_symbol": "AAPL"}, headers=headers
        ).status_code
        == 400
    )
    assert db.query(PortfoliosTable).count() == 1


def test_account_deletion_requires_post_and_removes_only_its_owner(
    client, make_user, db
):
    owner, headers = make_user()
    other, _ = make_user("other@example.com")
    owner_id, other_id = owner.id, other.id
    seed_portfolio(db, owner, 101)
    seed_portfolio(db, other, 999)
    db.add(EmailReminderDelivery(user_id=owner.id, local_date=date(2026, 1, 1)))
    db.commit()
    token = create_account_deletion_token(owner.email, owner.hashed_password)
    assert (
        client.get("/user/confirm-delete-account", params={"token": token}).status_code
        == 405
    )
    assert db.get(UsersTable, owner_id) is not None
    assert (
        client.post("/user/confirm-delete-account", params={"token": token}).status_code
        == 200
    )
    db.expire_all()
    assert db.get(UsersTable, owner_id) is None
    assert db.get(UsersTable, other_id) is not None
    assert db.query(EmailReminderDelivery).count() == 0
    assert db.query(PortfoliosTable).filter_by(user_id=owner_id).count() == 0
    assert db.query(StockDataCache).filter_by(user_id=owner_id).count() == 0
    assert db.query(PortfoliosTable).filter_by(user_id=other_id).count() == 1
    assert client.get("/portfolio/summary", headers=headers).status_code == 401


def test_stale_deletion_token_preserves_user(client, make_user, db):
    user, _ = make_user()
    token = create_account_deletion_token(user.email, user.hashed_password)
    user.hashed_password = bcrypt.hashpw(
        b"NewStrongPass2!", bcrypt.gensalt(rounds=4)
    ).decode()
    db.commit()
    assert (
        client.post("/user/confirm-delete-account", params={"token": token}).status_code
        == 401
    )
    assert db.query(UsersTable).count() == 1
