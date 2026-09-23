import logging
from uuid import UUID

import redis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis_client import redis_client
from app.models.membership import Membership
from app.schemas.membership import MembershipResponse

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 30


def get_membership(db: Session, user_id: UUID) -> MembershipResponse | None:
    cache_key = f"membership:by-user:{user_id}"

    #Intenta leer desde Redis.
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return MembershipResponse.model_validate_json(cached)
    except (redis.RedisError, ValueError):
        #Si Redis falla o el contenido no es válido, continúa con PostgreSQL.
        logger.warning("Membership cache unavailable or invalid", exc_info=True)

    #Si no está en caché, consulta PostgreSQL.
    try:
        statement = (
            select(Membership)
            .where(Membership.user_id == user_id)
            .order_by(Membership.created_at.desc())
        )
        membership = db.execute(statement).scalars().first()
    except SQLAlchemyError as exc:
        logger.exception("Database error while getting membership")
        raise HTTPException(
            status_code=500,
            detail="Error connecting to the database",
        ) from exc

    if membership is None:
        return None

    #Convierte el ORM a respuesta y guarda JSON en Redis.
    response = MembershipResponse.model_validate(membership)

    try:
        redis_client.set(
            cache_key,
            response.model_dump_json(),
            ex=CACHE_TTL_SECONDS,
        )
    except redis.RedisError:
        #Redis es caché: si falla el guardado, aún se devuelve el resultado de PostgreSQL.
        logger.warning("Could not write membership to cache", exc_info=True)

    return response