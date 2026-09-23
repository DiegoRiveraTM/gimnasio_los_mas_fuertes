from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.membership import MembershipStatus, TypeOfMembership


class MembershipResponse(BaseModel):
    id: UUID
    membership_type: TypeOfMembership
    monthly_cost: Decimal
    status: MembershipStatus
    active_since: datetime
    next_payment_at: datetime

    model_config = ConfigDict(from_attributes=True)