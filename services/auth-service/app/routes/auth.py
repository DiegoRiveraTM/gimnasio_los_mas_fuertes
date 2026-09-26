from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from uuid import UUID
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.limiter import limiter
from app.db.db import get_session
from app.models.user import User
from app.schemas.user import LoginForm, Token, UserCreate, UserResponse
from app.services.auth import (
    login_user as login_user_service,
    register_user as register_user_service,
)

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise unauthorized from exc

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise unauthorized

    return user


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
    
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
