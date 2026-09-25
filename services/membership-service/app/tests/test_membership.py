from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import jwt
from app.core.config import settings
from app.models.membership import Membership, TypeOfMembership


def test_obtener_mi_membresia(client, db):
    user_id = uuid4()

    db.add(
        Membership(
            user_id=user_id,
            membership_type=TypeOfMembership.bronze,
            monthly_cost=Decimal("400.00"),
            next_payment_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    db.commit()

    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    response = client.get(
        "/memberships/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["membership_type"] == "bronze"