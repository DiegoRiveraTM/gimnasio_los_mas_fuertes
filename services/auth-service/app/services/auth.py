from fastapi import HTTPException
from models import User
from schemas import UserCreate, Token
from core.security import get_password_hash, verify_password, create_access_token
from sqlalchemy.orm import Session
from datetime import timedelta
from core.config import settings
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def register_user(user: UserCreate, db: Session):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="A User With That Email Already Exists")
        hashed = get_password_hash(user.password)
        new_user = User(username=user.username, email=user.email, password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error Connecting to the Database")
        

def login_user(form_data, db: Session):
    try:
        user_exists = db.query(User).filter(User.email == form_data.email).first()
        
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Username or Email already Exists"
            )
        if not user_exists:
            logger.warning(f"Failed login - email not found: {form_data.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        is_valid = verify_password(form_data.password, user_exists.password)
        if not is_valid:
            logger.warning(f"Failed login - wrong password for user_id: {user_exists.id}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"Successful login for user_id: {user_exists.id}")
        
        access_token = create_access_token(
            subject=user_exists.email,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return Token(access_token=access_token, token_type="bearer")
    
    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")