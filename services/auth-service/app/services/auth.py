import logging
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.user import LoginForm, Token, UserCreate
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def register_user(user: UserCreate, db: Session):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="A User With That Email Already Exists")
        hashed = get_password_hash(user.password)
        new_user = User(username=user.username, email=user.email, password_hash=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error Connecting to the Database")
        

def login_user(form_data: LoginForm, db: Session) -> Token:
    try:
        user = db.query(User).filter(
            User.email == form_data.email
        ).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        if not verify_password(form_data.password, user.password_hash):
            logger.warning("Failed login: invalid password")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
        )

    except SQLAlchemyError as exc:
        logger.exception("Database error during login")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from exc