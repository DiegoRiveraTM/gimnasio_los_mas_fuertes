import enum
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Enum as SAEnum, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.db import Base


class TypeOfMembership(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"


class MembershipStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    expired = "expired"


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True
    )
    membership_type: Mapped[TypeOfMembership] = mapped_column(
        SAEnum(TypeOfMembership, name="membership_type"),
        nullable=False,
    )
    monthly_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    status: Mapped[MembershipStatus] = mapped_column(
        SAEnum(MembershipStatus, name="membership_status"),
        nullable=False,
        default=MembershipStatus.active,
    )
    active_since: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    next_payment_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )