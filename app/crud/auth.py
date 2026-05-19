from datetime import datetime, timedelta
from app.db import models
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
import jwt
import os

key = os.environ.get("KEY")
algorithm = os.environ.get("ALGORITHM")
token_expire_time = 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


def create_access_token(user_id: int) -> str:
    expire = datetime.now(datetime.timezone.ist) + timedelta(days=token_expire_time)
    details = {
        "user_id": str(user_id),
        "exp": expire
    }
    return jwt.encode(details, key, algorithm=algorithm)
    
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(token, key, algorithms=[algorithm])
        return token_data
    except jwt.ExpiredSignatureError:
        return {"error": "token expired"}
    except jwt.PyJWTError:
        return {"error": "invalid token"}
    
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()