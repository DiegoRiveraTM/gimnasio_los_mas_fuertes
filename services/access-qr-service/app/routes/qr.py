from fastapi import APIRouter, Depends, Request
from app.core.limiter import limiter
from app.deps import AuthenticatedUser, get_current_user
from app.schemas.qr import (
    QRCodeResponse,
    QRValidationRequest,
    QRValidationResponse,
)
from app.services.qr import consume_access_qr, generate_access_qr
from app.core.scanner_auth import require_scanner_key

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

@router.post("/validate", response_model=QRValidationResponse)
@limiter.limit("30/minute")
async def validate_qr(request: Request, payload: QRValidationRequest):
    return await consume_access_qr(payload.access_code)

@router.post("/validate", response_model=QRValidationResponse)
@limiter.limit("30/minute")
async def validate_qr(
    request: Request,
    payload: QRValidationRequest,
    _authorized: bool = Depends(require_scanner_key),
):
    return await consume_access_qr(payload.access_code)