from database import Base, engine

# Import the models so SQLAlchemy registers every table with Base.metadata.
import models  # noqa: F401


def init_database() -> None:
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("Database schema is ready.")


if __name__ == "__main__":
    init_database()