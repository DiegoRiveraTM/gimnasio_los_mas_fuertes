from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))

class Base(DeclarativeBase):
    pass

def get_session():
    with Session(engine) as session:
        yield session