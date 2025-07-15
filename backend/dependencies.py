from fastapi import Depends, HTTPException 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from jose import JWTError
from utils.jwt import decode_token

security = HTTPBearer()

def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials  # Extract token string from "Bearer <token>"
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not isinstance(email, str):
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
