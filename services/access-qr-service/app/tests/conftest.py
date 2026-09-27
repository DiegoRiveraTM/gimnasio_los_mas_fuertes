import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from app.core.limiter import limiter
from app.main import app
from datetime import UTC, datetime, timedelta
from uuid import uuid4
import jwt
import pytest
from app.core.config import settings


@pytest.fixture
def auth_token():
    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )

@pytest.fixture(autouse=True)
def disable_rate_limiter():
    previous_value = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = previous_value


@pytest.fixture
def fake_redis(monkeypatch):
    from app.services import qr as qr_service

    redis = fakeredis.aioredis.FakeRedis(
        encoding="utf-8",
        decode_responses=True,
    )
    monkeypatch.setattr(qr_service, "redis_client", redis)
    return redis


@pytest.fixture
def client(monkeypatch, fake_redis):
    from app.services import qr as qr_service

    async def fake_get_membership(access_token: str):
        return {
            "status": "active",
            "next_payment_at": (
                datetime.now(UTC) + timedelta(days=30)
            ).isoformat(),
        }

    monkeypatch.setattr(qr_service, "get_membership", fake_get_membership)

    with TestClient(app) as test_client:
        yield test_client