# app/db/db.py
from app.core.config import settings
# app/routes/auth.py
from app.db.db import get_session
from app.schemas.user import UserCreate, UserResponse, Token, LoginForm
from app.services.auth import register_user_service, login_user_service
from app.core.limiter import limiter
from app.models.user import User
# app/services/auth.py
from app.models.user import User
from app.schemas.user import UserCreate, Token
from app.core.security import ...
from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")