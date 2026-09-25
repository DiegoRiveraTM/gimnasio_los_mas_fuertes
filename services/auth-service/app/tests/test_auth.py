import pytest

def test_registrar_usuario(client):
    response = client.post("/auth/register", json={
        "username": "Test",
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })
    assert response.status_code == 200, response.text

def test_login_usuario(client):
    client.post("/auth/register", json={
        "username": "Test",
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })
    response = client.post("/auth/login", json={
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })
    assert response.status_code == 200

@pytest.fixture
def auth_token(client):
    response = client.post("/auth/register", json={
        "username": "Test",
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })
    assert response.status_code == 200

    response = client.post("/auth/login", json={
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })
    assert response.status_code == 200

    token = response.json()["access_token"]
    return token