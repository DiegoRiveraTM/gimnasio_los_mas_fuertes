from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QRCodeResponse(BaseModel):
    #Data URI de la imagen PNG; se puede asignar directamente a src en el frontend.
    qr_code: str
    expires_at: datetime
    expires_in_seconds: int


class QRValidationRequest(BaseModel):
    access_code: str = Field(min_length=32, max_length=128)


class QRValidationResponse(BaseModel):
    valid: bool
    user_id: UUID | None = None