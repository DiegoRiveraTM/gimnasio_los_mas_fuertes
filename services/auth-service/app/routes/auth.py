from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from db.db import get_session
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, UserResponse, Token, LoginForm
from services.auth import register_user as register_user_service, login_user as login_user_service
from core.limiter import limiter
from deps import get_current_user
from models.user import User

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

@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    return current_user