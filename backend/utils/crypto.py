from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from config import get_settings


ENCRYPTED_PREFIX = "enc:v1:"


def _get_fernet() -> Fernet:
    settings = get_settings()

    try:
        return Fernet(
            settings.API_KEY_ENCRYPTION_KEY.encode("utf-8")
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "API_KEY_ENCRYPTION_KEY must be a valid Fernet key"
        ) from exc


def is_encrypted_secret(value: str) -> bool:
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_secret(value: str) -> str:
    if not value:
        return value

    if is_encrypted_secret(value):
        return value

    token = _get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("utf-8")

    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_secret(value: str) -> str:
    if not value:
        return value

    if not is_encrypted_secret(value):
        # Backward compatibility for rows created before encryption
        # was introduced. init_db.py migrates these values in-place.
        return value

    token = value[len(ENCRYPTED_PREFIX):]

    try:
        return _get_fernet().decrypt(
            token.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Stored encrypted secret could not be decrypted"
        ) from exc


class EncryptedText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(
        self,
        value: str | None,
        dialect,
    ) -> str | None:
        if value is None:
            return None

        return encrypt_secret(value)

    def process_result_value(
        self,
        value: str | None,
        dialect,
    ) -> str | None:
        if value is None:
            return None

        return decrypt_secret(value)