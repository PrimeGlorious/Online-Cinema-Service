from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from users.models import User
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    # Dummy реалізація — замінити на декодування JWT
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def require_moderator(user: User = Depends(get_current_user)):
    if not user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator rights required")
    return user
