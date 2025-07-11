from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from utils.jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = decode_token(token)
        email = payload.get("sub")

        if not isinstance(email, str):
            raise HTTPException(status_code=401, detail="Invalid token")

        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
