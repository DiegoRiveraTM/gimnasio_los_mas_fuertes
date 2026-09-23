from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


async def get_membership(access_token: str) -> dict[str, Any] | None:
    url = f"{settings.MEMBERSHIP_SERVICE_URL.rstrip('/')}/memberships/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Membership service is unavailable",
        ) from exc

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    if response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication was rejected by membership service",
        )

    if response.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Membership service returned an error",
        )

    return response.json()