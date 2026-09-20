import os
import unittest

from cryptography.fernet import Fernet


os.environ.setdefault(
    "API_KEY_ENCRYPTION_KEY",
    Fernet.generate_key().decode("utf-8"),
)
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///:memory:",
)
os.environ.setdefault(
    "EMAIL_ADDRESS",
    "test@example.com",
)
os.environ.setdefault(
    "EMAIL_PASSWORD",
    "test-password",
)
os.environ.setdefault(
    "JWT_SECRET",
    "test-jwt-secret-that-is-long-enough-for-tests",
)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database import Base
from models import UsersTable
from utils.crypto import (
    decrypt_secret,
    encrypt_secret,
    is_encrypted_secret,
)


class ApiKeyEncryptionTests(unittest.TestCase):
    def test_crypto_round_trip(self):
        plaintext = "TEST_ALPHA_VANTAGE_KEY_1234"

        encrypted = encrypt_secret(plaintext)

        self.assertNotEqual(encrypted, plaintext)
        self.assertTrue(is_encrypted_secret(encrypted))
        self.assertEqual(
            decrypt_secret(encrypted),
            plaintext,
        )

    def test_legacy_plaintext_can_still_be_read(self):
        legacy_plaintext = "LEGACY_KEY_1234"

        self.assertEqual(
            decrypt_secret(legacy_plaintext),
            legacy_plaintext,
        )

    def test_model_encrypts_database_value_transparently(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            plaintext = "DATABASE_TEST_KEY_1234"

            user = UsersTable(
                email="crypto-test@example.com",
                hashed_password="test-hash",
                is_verified=True,
                alpha_vantage_api_key=plaintext,
            )

            db.add(user)
            db.commit()

            with engine.connect() as connection:
                stored_value = connection.execute(
                    text(
                        """
                        SELECT alpha_vantage_api_key
                        FROM users_table
                        WHERE id = :user_id
                        """
                    ),
                    {"user_id": user.id},
                ).scalar_one()

            self.assertNotEqual(stored_value, plaintext)
            self.assertTrue(
                is_encrypted_secret(stored_value)
            )

            db.expire_all()

            loaded_user = (
                db.query(UsersTable)
                .filter(UsersTable.id == user.id)
                .one()
            )

            self.assertEqual(
                loaded_user.alpha_vantage_api_key,
                plaintext,
            )

        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()