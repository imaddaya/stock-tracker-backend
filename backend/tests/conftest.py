"""Isolated API tests; no real email, market API or application database."""

import os
import sys
from pathlib import Path

import bcrypt
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(
    DATABASE_URL="sqlite:///:memory:",
    EMAIL_ADDRESS="test@example.com",
    EMAIL_PASSWORD="unused-test-password",
    JWT_SECRET="isolated-api-test-secret-never-use-in-production",
    API_KEY_ENCRYPTION_KEY=Fernet.generate_key().decode(),
)
from database import Base, get_db, normalize_database_url
from main import app
from models import UsersTable
from utils.jwt import create_access_token


@pytest.fixture
def db():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    kwargs = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if url.startswith("sqlite")
        else {}
    )
    engine = create_engine(normalize_database_url(url), **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db, monkeypatch):
    def override_db():
        yield db

    def unexpected_network(*_args, **_kwargs):
        raise AssertionError("External email/market API must be mocked in tests")

    import httpx
    import smtplib

    monkeypatch.setattr(httpx, "get", unexpected_network)
    monkeypatch.setattr(smtplib, "SMTP_SSL", unexpected_network)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def create(email="owner@example.com", verified=True):
        user = UsersTable(
            email=email,
            hashed_password=bcrypt.hashpw(
                b"StrongPass1!", bcrypt.gensalt(rounds=4)
            ).decode(),
            is_verified=verified,
            alpha_vantage_api_key="FAKE_TEST_KEY",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        headers = {
            "Authorization": f"Bearer {create_access_token(user.email, user.hashed_password)}"
        }
        return user, headers

    return create
