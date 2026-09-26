from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class QRCodeResponse(BaseModel):
    qr_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    qr_code: str
    expires_at: datetime
    expires_in_seconds: int


class QRValidationRequest(BaseModel):
    access_code: str = Field(min_length=32, max_length=128)


class QRValidationResponse(BaseModel):
    valid: bool
    user_id: UUID | None = None
    reason: Literal["cooldown", "invalid_or_expired"] | None = None
    retry_after_seconds: int = Field(default=0, ge=0)


class QRStatusResponse(BaseModel):
    qr_id: str
    state: Literal["pending", "used", "expired"]
