from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import get_settings

settings = get_settings()

# ✅ No need for check_same_thread anymore
engine = create_engine(
    settings.DATABASE_URL,
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
