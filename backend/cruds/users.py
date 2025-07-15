from sqlalchemy.orm import Session
from models import UsersTable
from schemas import UserSignup
import bcrypt

def create_user(db: Session, user: UserSignup):
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    db_user = UsersTable(
        email=user.email,
        hashed_password=hashed_pw.decode("utf-8"),
        is_verified=False,
        alpha_vantage_api_key=user.alpha_vantage_api_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(UsersTable).filter(UsersTable.email == email).first()

def verify_user(db: Session, email: str):
    user = get_user_by_email(db, email)
    if user:
        user.is_verified = True
        db.commit()
    return user

def update_password(db: Session, email: str, new_password: str):
    user = get_user_by_email(db, email)
    if user:
        hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        user.hashed_password = hashed_pw.decode("utf-8")
        db.commit()
    return user
