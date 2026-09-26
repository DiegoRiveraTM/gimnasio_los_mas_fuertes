import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import fakeredis.aioredis
import pytest
from fastapi import HTTPException

from app.services import qr as service


async def prepare(monkeypatch):
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(service, "redis_client", client)
    monkeypatch.setattr(service, "get_membership", AsyncMock(return_value={"status": "active"}))
    monkeypatch.setattr(service, "_make_qr_data_uri", lambda _: "data:image/png;base64,dGVzdA==")
    codes = iter(["A" * 43, "B" * 43, "C" * 43])
    monkeypatch.setattr(service.secrets, "token_urlsafe", lambda _: next(codes))
    return client


def test_old_qr_is_rejected_during_cooldown_and_attempt_does_not_extend_it(monkeypatch):
    async def run():
        client = await prepare(monkeypatch)
        try:
            owner = uuid4()
            await service.generate_access_qr(owner, "test")
            second = await service.generate_access_qr(owner, "test")
            assert (await service.consume_access_qr("A" * 43)).valid is True
            key = service._cooldown_key(str(owner))
            before = await client.pttl(key)
            assert 0 < before <= 180_000
            rejected = await service.consume_access_qr("B" * 43)
            assert rejected.valid is False
            assert rejected.reason == "cooldown"
            assert 0 < rejected.retry_after_seconds <= 180
            assert 0 < await client.pttl(key) <= before
            assert (await service.read_access_qr_status(second.qr_id, owner)).state == "pending"
        finally:
            await client.aclose()
    asyncio.run(run())


def test_generation_is_blocked_after_success(monkeypatch):
    async def run():
        client = await prepare(monkeypatch)
        try:
            owner = uuid4()
            await service.generate_access_qr(owner, "test")
            await service.consume_access_qr("A" * 43)
            with pytest.raises(HTTPException) as error:
                await service.generate_access_qr(owner, "test")
            assert error.value.status_code == 429
            assert int(error.value.headers["Retry-After"]) > 0
        finally:
            await client.aclose()
    asyncio.run(run())


def test_another_user_can_enter(monkeypatch):
    async def run():
        client = await prepare(monkeypatch)
        try:
            await service.generate_access_qr(uuid4(), "test")
            await service.generate_access_qr(uuid4(), "test")
            assert (await service.consume_access_qr("A" * 43)).valid is True
            assert (await service.consume_access_qr("B" * 43)).valid is True
        finally:
            await client.aclose()
    asyncio.run(run())


def test_new_access_after_cooldown_ends(monkeypatch):
    async def run():
        client = await prepare(monkeypatch)
        try:
            owner = uuid4()
            await service.generate_access_qr(owner, "test")
            await service.consume_access_qr("A" * 43)
            # Simula el fin del bloqueo sin esperar tres minutos.
            await client.delete(service._cooldown_key(str(owner)))
            await service.generate_access_qr(owner, "test")
            assert (await service.consume_access_qr("B" * 43)).valid is True
        finally:
            await client.aclose()
    asyncio.run(run())


def test_simultaneous_qrs_accept_only_one_access(monkeypatch):
    async def run():
        client = await prepare(monkeypatch)
        try:
            owner = uuid4()
            await service.generate_access_qr(owner, "test")
            await service.generate_access_qr(owner, "test")
            results = await asyncio.gather(
                service.consume_access_qr("A" * 43),
                service.consume_access_qr("B" * 43),
            )
            assert sum(result.valid for result in results) == 1
            assert next(result for result in results if not result.valid).reason == "cooldown"
        finally:
            await client.aclose()
    asyncio.run(run())
