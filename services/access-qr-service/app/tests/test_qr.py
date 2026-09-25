import base64


def test_generar_qr_requiere_jwt(client):
    response = client.post("/qr/me")

    assert response.status_code == 401, response.text


def test_generar_qr_devuelve_imagen_y_expiracion(client, auth_token):
    response = client.post(
        "/qr/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200, response.text

    body = response.json()
    qr_code = body["qr_code"]

    assert qr_code.startswith("data:image/png;base64,")
    image_bytes = base64.b64decode(qr_code.split(",", 1)[1])
    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert body["expires_in_seconds"] == 60
    assert body["expires_at"]