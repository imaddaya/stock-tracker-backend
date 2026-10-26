from sqlalchemy import create_engine
from database import normalize_database_url


def test_legacy_postgres_url_loads_the_installed_driver_without_connecting():
    url = normalize_database_url(
        "postgresql://test:p%40ss%3Aword@localhost/test_database?sslmode=require"
    )
    engine = create_engine(url)
    try:
        assert engine.dialect.driver == "psycopg2"
        assert engine.dialect.dbapi.__name__ == "psycopg2"
        assert engine.url.password == "p@ss:word"
        assert engine.url.query["sslmode"] == "require"
        assert normalize_database_url(engine.url) == engine.url
    finally:
        engine.dispose()
