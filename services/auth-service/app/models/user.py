import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.db import Base

class Role(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role"),
        nullable=False,
        default=Role.MEMBER
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )