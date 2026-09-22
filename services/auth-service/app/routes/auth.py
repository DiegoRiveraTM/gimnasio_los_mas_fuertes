from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.db import get_session
from app.models.user import User
from app.schemas.user import LoginForm, Token, UserCreate, UserResponse
from app.services.auth import (
    login_user as login_user_service,
    register_user as register_user_service,
)

router = APIRouter()

@router.post("/register", response_model= UserResponse)
@limiter.limit("5/minute")
def register_user(
    request: Request,
    user: UserCreate, 
    db: Session = Depends(get_session)):
    return register_user_service(user,db)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login_user(
    request: Request,
    form_data: LoginForm,
    db: Session = Depends(get_session)
):
    return login_user_service(form_data, db)
