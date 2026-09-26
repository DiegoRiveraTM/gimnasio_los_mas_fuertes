import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_scanner_key(
    x_scanner_api_key: str | None = Header(
        default=None,
        alias="X-Scanner-Api-Key",
    ),
) -> bool:
    expected = settings.QR_SCANNER_API_KEY.get_secret_value()

    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scanner authentication is not configured",
        )

    if not x_scanner_api_key or not secrets.compare_digest(
        x_scanner_api_key.encode("utf-8"),
        expected.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scanner authentication required",
        )

    return True