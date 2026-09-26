from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.core.limiter import limiter
from app.core.scanner_auth import require_scanner_key
from app.deps import AuthenticatedUser, get_current_user
from app.schemas.qr import (
    QRCodeResponse,
    QRStatusResponse,
    QRValidationRequest,
    QRValidationResponse,
)
from app.services.qr import (
    consume_access_qr,
    generate_access_qr,
    read_access_qr_status,
)

router = APIRouter()


@router.post("/me", response_model=QRCodeResponse)
@limiter.limit("5/minute")
async def issue_my_qr(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return await generate_access_qr(
        user_id=current_user.id,
        access_token=current_user.access_token,
    )


@router.get("/status/{qr_id}", response_model=QRStatusResponse)
@limiter.limit("60/minute")
async def qr_status(
    request: Request,
    qr_id: Annotated[str, Path(pattern=r"^[0-9a-f]{64}$")],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return await read_access_qr_status(qr_id, current_user.id)


@router.post("/validate", response_model=QRValidationResponse)
@limiter.limit("30/minute")
async def validate_qr(
    request: Request,
    payload: QRValidationRequest,
    _authorized: bool = Depends(require_scanner_key),
):
    return await consume_access_qr(payload.access_code)
