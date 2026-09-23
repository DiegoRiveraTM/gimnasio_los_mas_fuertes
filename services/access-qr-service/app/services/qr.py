import base64
import hashlib
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID
import secrets
from app.schemas.qr import QRValidationResponse
import qrcode
from fastapi import HTTPException, status
from redis.exceptions import RedisError
from app.core.redis_client import redis_client
from app.schemas.qr import QRCodeResponse
from app.services.membership_client import get_membership


QR_TTL_SECONDS = 60


def _make_qr_data_uri(access_code: str) -> str:
    image = qrcode.make(access_code)
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


async def generate_access_qr(
    user_id: UUID,
    access_token: str,
) -> QRCodeResponse:
    membership = await get_membership(access_token)

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )

    if membership.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An active membership is required",
        )

    #El QR contiene un código aleatorio de un solo uso, no el JWT.
    access_code = secrets.token_urlsafe(32)
    code_hash = hashlib.sha256(access_code.encode("utf-8")).hexdigest()
    redis_key = f"qr:access:{code_hash}"

    try:
        stored = await redis_client.set(
            redis_key,
            str(user_id),
            ex=QR_TTL_SECONDS,
            nx=True,
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QR storage is unavailable",
        ) from exc

    if not stored:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create an access QR code",
        )

    return QRCodeResponse(
        qr_code=_make_qr_data_uri(access_code),
        expires_at=datetime.now(UTC) + timedelta(seconds=QR_TTL_SECONDS),
        expires_in_seconds=QR_TTL_SECONDS,
    )
async def consume_access_qr(access_code: str) -> QRValidationResponse:
    code_hash = hashlib.sha256(access_code.encode("utf-8")).hexdigest()
    redis_key = f"qr:access:{code_hash}"

    try:
        # GETDEL obtiene y borra la clave atómicamente: no se puede reutilizar.
        user_id = await redis_client.getdel(redis_key)
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="QR storage is unavailable",
        ) from exc

    if user_id is None:
        return QRValidationResponse(valid=False)

    return QRValidationResponse(valid=True, user_id=UUID(user_id))
