from fastapi import HTTPException, status
import bcrypt  ## hash the password 
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

import src.config as sec ## security Configs
from src.Model.User import TokenData ## Pydantic Models


def verify_Password(plain_pwd : str, hashed_pwd : str) -> bool:
    return bcrypt.checkpw(plain_pwd.encode('utf-8'), hashed_pwd.encode('utf-8'))

def get_pwd_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # 1)create a copy
    to_encode = data.copy()
    # 2) set expiration based on the expire given or set it to default as 15  
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=15)
    # 3) update the exp and encode using jwt.encode()
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, sec.SECRET_KEY, algorithm= sec.ALGORITHM)
    return encoded_jwt
    
def verify_token(token : str) -> TokenData:
    try:
        payload = jwt.decode(token=token,  key= sec.SECRET_KEY ,algorithms=[sec.ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )