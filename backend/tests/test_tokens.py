from datetime import timedelta
import jwt
from config import get_settings
from utils.jwt import create_access_token, create_token


def test_tampered_signature_is_rejected(client, make_user):
    user, _ = make_user()
    header, payload, signature = create_access_token(
        user.email, user.hashed_password
    ).split(".")
    changed = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert (
        client.get(
            "/portfolio/summary",
            headers={"Authorization": f"Bearer {header}.{payload}.{changed}"},
        ).status_code
        == 401
    )


def test_expired_token_is_rejected(client, make_user):
    user, _ = make_user()
    token = create_token({"sub": user.email, "type": "access"}, timedelta(seconds=-1))
    response = client.get(
        "/portfolio/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_signed_token_without_expiry_is_rejected(client, make_user):
    user, _ = make_user()
    settings = get_settings()
    token = jwt.encode(
        {"sub": user.email, "type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.get(
            "/portfolio/summary", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )
