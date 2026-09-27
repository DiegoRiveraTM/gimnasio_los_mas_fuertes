import base64
import hashlib
import secrets
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

import qrcode
from fastapi import HTTPException
from redis.exceptions import RedisError, WatchError

from app.core.redis_client import redis_client
from app.schemas.qr import QRCodeResponse, QRStatusResponse, QRValidationResponse
from app.services.membership_client import get_membership
from app.services.membership_validity import parse_membership_expiration

QR_TTL_SECONDS = 60
ACCESS_COOLDOWN_SECONDS = 180


def _cooldown_key(user_id: str) -> str:
    return f"qr:user:{user_id}:cooldown"
# Conserva el resultado unos minutos, NO la validez del acceso.
QR_STATUS_TTL_SECONDS = 300


def _keys(qr_id: str) -> tuple[str, str]:
    # Ambas claves comparten hash tag para Redis Cluster.
    return f"qr:{{{qr_id}}}:access:v2", f"qr:{{{qr_id}}}:status:v2"


def _make_qr_data_uri(access_code: str) -> str:
    image = qrcode.make(access_code)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


async def generate_access_qr(user_id: UUID, access_token: str) -> QRCodeResponse:
    membership = await get_membership(access_token)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    if membership.get("status") != "active":
        raise HTTPException(status_code=403, detail="An active membership is required")
    try:
        membership_expires_at = parse_membership_expiration(membership.get("next_payment_at"))
    except ValueError as exc:
        # No concede acceso cuando falta la fecha o viene sin zona horaria.
        raise HTTPException(status_code=502, detail="Membership expiration data is invalid") from exc
    if membership_expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=403, detail="Membership has expired")

    try:
        remaining_ms = await redis_client.pttl(_cooldown_key(str(user_id)))
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="QR storage is unavailable") from exc
    if remaining_ms == -1:
        raise HTTPException(status_code=503, detail="Access cooldown configuration is invalid")
    if remaining_ms > 0:
        seconds = (remaining_ms + 999) // 1000
        raise HTTPException(
            status_code=429,
            detail=f"Wait {seconds} seconds before requesting another access QR",
            headers={"Retry-After": str(seconds)},
        )

    access_code = secrets.token_urlsafe(32)
    qr_id = hashlib.sha256(access_code.encode("utf-8")).hexdigest()
    image_uri = _make_qr_data_uri(access_code)
    access_key, status_key = _keys(qr_id)

    try:
        server_seconds, microseconds = await redis_client.time()
        server_timestamp = server_seconds + microseconds / 1_000_000
        # Redis es la autoridad del TTL. Nunca mantener el QR más allá de la membresía.
        remaining_membership_seconds = int(membership_expires_at.timestamp() - server_timestamp)
        qr_ttl = min(QR_TTL_SECONDS, remaining_membership_seconds)
        if qr_ttl <= 0:
            raise HTTPException(status_code=403, detail="Membership has expired")
        expires_timestamp = server_timestamp + qr_ttl
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.set(access_key, str(user_id), ex=qr_ttl, nx=True)
            pipe.hset(status_key, mapping={
                "user_id": str(user_id),
                "state": "pending",
                "expires_at": str(expires_timestamp),
            })
            pipe.expire(status_key, QR_STATUS_TTL_SECONDS)
            results = await pipe.execute()
        if not results[0]:
            raise HTTPException(status_code=503, detail="Could not create an access QR code")
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="QR storage is unavailable") from exc

    return QRCodeResponse(
        qr_id=qr_id,
        qr_code=image_uri,
        expires_at=datetime.fromtimestamp(expires_timestamp, UTC),
        expires_in_seconds=qr_ttl,
    )


async def consume_access_qr(access_code: str) -> QRValidationResponse:
    qr_id = hashlib.sha256(access_code.encode("utf-8")).hexdigest()
    access_key, status_key = _keys(qr_id)

    try:
        for _ in range(5):
            async with redis_client.pipeline(transaction=True) as pipe:
                try:
                    await pipe.watch(access_key, status_key)
                    user_id = await pipe.get(access_key)
                    if user_id is None:
                        return QRValidationResponse(valid=False, reason="invalid_or_expired")
                    record = await pipe.hgetall(status_key)
                    if record.get("state") != "pending" or record.get("user_id") != user_id:
                        return QRValidationResponse(valid=False)

                    cooldown_key = _cooldown_key(user_id)
                    await pipe.watch(cooldown_key)
                    remaining_ms = await pipe.pttl(cooldown_key)
                    if remaining_ms == -1:
                        raise HTTPException(status_code=503, detail="Access cooldown configuration is invalid")
                    if remaining_ms > 0:
                        return QRValidationResponse(
                            valid=False,
                            reason="cooldown",
                            retry_after_seconds=(remaining_ms + 999) // 1000,
                        )

                    # WATCH + MULTI/EXEC garantiza que solo un escáner consume
                    # el código y que estado + bloqueo cambian en la misma operación.
                    # Esta transacción entre usuarios/QR requiere Redis sin cluster mode.
                    pipe.multi()
                    pipe.delete(access_key)
                    pipe.hset(status_key, "state", "used")
                    pipe.set(cooldown_key, "1", ex=ACCESS_COOLDOWN_SECONDS)
                    await pipe.execute()
                    return QRValidationResponse(valid=True, user_id=UUID(user_id))
                except WatchError:
                    continue
        raise HTTPException(status_code=503, detail="Please retry QR validation")
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="QR storage is unavailable") from exc


async def read_access_qr_status(qr_id: str, user_id: UUID) -> QRStatusResponse:
    _, status_key = _keys(qr_id)
    try:
        record = await redis_client.hgetall(status_key)
        # No revela información de códigos ajenos ni permite consumirlos.
        if not record or record.get("user_id") != str(user_id):
            raise HTTPException(status_code=404, detail="QR not found")
        if record.get("state") == "used":
            return QRStatusResponse(qr_id=qr_id, state="used")
        server_seconds, microseconds = await redis_client.time()
        now = server_seconds + microseconds / 1_000_000
        state = "expired" if now >= float(record["expires_at"]) else "pending"
        return QRStatusResponse(qr_id=qr_id, state=state)
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="QR storage is unavailable") from exc
