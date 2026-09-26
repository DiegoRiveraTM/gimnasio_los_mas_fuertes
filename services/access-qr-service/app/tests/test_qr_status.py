import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import fakeredis.aioredis
import pytest
from fastapi import HTTPException

from app.services import qr as qr_service


async def _prepare(monkeypatch):
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(qr_service, "redis_client", client)
    monkeypatch.setattr(
        qr_service, "get_membership",
        AsyncMock(return_value={"status": "active"}),
    )
    monkeypatch.setattr(qr_service.secrets, "token_urlsafe", lambda _: "A" * 43)
    monkeypatch.setattr(
        qr_service, "_make_qr_data_uri",
        lambda _: "data:image/png;base64,dGVzdA==",
    )
    owner = uuid4()
    result = await qr_service.generate_access_qr(owner, "test-token")
    return client, owner, result


def test_status_changes_to_used_and_code_cannot_be_reused(monkeypatch):
    async def run():
        client, owner, result = await _prepare(monkeypatch)
        try:
            assert (await qr_service.read_access_qr_status(result.qr_id, owner)).state == "pending"
            first = await qr_service.consume_access_qr("A" * 43)
            assert first.valid is True
            assert first.user_id == owner
            assert (await qr_service.read_access_qr_status(result.qr_id, owner)).state == "used"
            assert (await qr_service.consume_access_qr("A" * 43)).valid is False
        finally:
            await client.aclose()
    asyncio.run(run())


def test_expired_is_not_used(monkeypatch):
    async def run():
        client, owner, result = await _prepare(monkeypatch)
        try:
            access_key, status_key = qr_service._keys(result.qr_id)
            # Simula las dos condiciones de expiración sin esperar 60 segundos.
            await client.delete(access_key)
            await client.hset(status_key, "expires_at", "0")
            assert (await qr_service.read_access_qr_status(result.qr_id, owner)).state == "expired"
            assert (await qr_service.consume_access_qr("A" * 43)).valid is False
        finally:
            await client.aclose()
    asyncio.run(run())


def test_another_user_cannot_read_status(monkeypatch):
    async def run():
        client, _, result = await _prepare(monkeypatch)
        try:
            with pytest.raises(HTTPException) as error:
                await qr_service.read_access_qr_status(result.qr_id, uuid4())
            assert error.value.status_code == 404
        finally:
            await client.aclose()
    asyncio.run(run())


def test_concurrent_validation_accepts_only_once(monkeypatch):
    async def run():
        client, _, _ = await _prepare(monkeypatch)
        try:
            results = await asyncio.gather(
                qr_service.consume_access_qr("A" * 43),
                qr_service.consume_access_qr("A" * 43),
            )
            assert sum(result.valid for result in results) == 1
        finally:
            await client.aclose()
    asyncio.run(run())

