from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import get_settings

settings = get_settings()


def normalize_database_url(value: str | URL) -> URL:
    """Keep legacy PostgreSQL URLs on the driver declared by this project."""
    url = make_url(value)
    if url.drivername == "postgresql":
        return url.set(drivername="postgresql+psycopg2")
    return url

# ✅ No need for check_same_thread anymore
engine = create_engine(
    normalize_database_url(settings.DATABASE_URL),
    echo=False  # optional: prints SQL statements to console
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ✅ Dependency to get a DB session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
