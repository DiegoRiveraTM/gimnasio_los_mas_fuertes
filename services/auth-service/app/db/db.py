from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase

engine = create_engine(str(settings.DATABASE_URL))

class Base(DeclarativeBase):
    pass

def get_session():
    with Session(engine) as session:
        yield session