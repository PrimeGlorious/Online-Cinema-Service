from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from movies.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
