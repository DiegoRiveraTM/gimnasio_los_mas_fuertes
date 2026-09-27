from datetime import UTC, datetime


def parse_membership_expiration(value: object) -> datetime:
    """Interpreta la fecha ISO 8601 de membership-service y exige zona horaria."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Membership expiration is missing")
    try:
        expiration = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Membership expiration is invalid") from exc
    if expiration.tzinfo is None or expiration.utcoffset() is None:
        raise ValueError("Membership expiration must include a timezone")
    return expiration.astimezone(UTC)