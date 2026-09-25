def test_invalid_email_format(client):
    response = client.post("/auth/register", json={
        "username": "test",
        "email": "admin@test.com'; DELETE FROM user; --",
        "password": "Password123"
    })
    assert response.status_code == 422