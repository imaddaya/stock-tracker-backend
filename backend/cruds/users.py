import bcrypt
from sqlalchemy.orm import Session

from models import UsersTable
from schemas import UserSignup


def create_user(db: Session, user: UserSignup) -> UsersTable:
    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    db_user = UsersTable(
        email=user.email,
        hashed_password=hashed_password,
        is_verified=False,
        alpha_vantage_api_key=user.alpha_vantage_api_key,
    )

    db.add(db_user)
    db.flush()
    db.refresh(db_user)

    return db_user


def get_user_by_email(db: Session, email: str):
    return (
        db.query(UsersTable)
        .filter(UsersTable.email == email)
        .first()
    )


def verify_user(db: Session, email: str):
    user = get_user_by_email(db, email)

    if user:
        user.is_verified = True
        db.commit()

    return user


def update_password(
    db: Session,
    email: str,
    new_password: str,
):
    user = get_user_by_email(db, email)

    if user:
        hashed_password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        user.hashed_password = hashed_password
        db.commit()

    return user