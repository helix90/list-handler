"""Tests for the security defaults: secret key, registration, CORS, password
hashes, tokens and the account administration command."""
import io
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import status
from pydantic import ValidationError

from app import manage
from app.auth import get_password_hash, verify_password
from app.config import Settings, settings
from app.models.user import User
from tests.conftest import TestingSessionLocal, engine

# Hashes made by the earlier passlib-based code, so existing accounts keep
# working: "testpassword", and "p" * 80 (longer than bcrypt's 72 bytes)
PASSLIB_HASH = "$2b$12$hlTul6cDUJ/lGXrv6j/TVOVu2UiBZymDy4b5jRXae/aeunYvCYPl6"
PASSLIB_LONG_HASH = "$2b$12$w4liYDUGSvCCNrdYYc1RfuaLEL5nH1GOBnU/Hi7BXLJBgkfQE/eE6"


class TestSecretKey:
    def test_missing_secret_key_is_refused(self, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(ValidationError, match="SECRET_KEY is not set"):
            Settings(_env_file=None)

    @pytest.mark.parametrize("key", ["your-secret-key-change-this-in-production", "short-key", "  " + "x" * 10 + "  "])
    def test_weak_secret_key_is_refused(self, key):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, secret_key=key)

    def test_strong_secret_key_is_accepted(self):
        key = "k" * 40
        assert Settings(_env_file=None, secret_key=key).secret_key == key

    def test_only_hmac_algorithms(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, secret_key="k" * 40, algorithm="none")

    def test_cors_origins_from_comma_separated_text(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://a.example, https://b.example")
        assert Settings(_env_file=None, secret_key="k" * 40).cors_origins == ["https://a.example", "https://b.example"]


class TestRegistrationClosedByDefault:
    def test_register_is_refused(self, client):
        assert settings.allow_registration is False
        response = client.post("/auth/register", json={"username": "mallory", "email": "m@example.com", "password": "pw123456"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "closed" in response.json()["detail"].lower()

    def test_register_works_when_allowed(self, client, open_registration):
        response = client.post("/auth/register", json={"username": "alice", "email": "a@example.com", "password": "pw123456"})
        assert response.status_code == status.HTTP_201_CREATED


class TestCORS:
    def test_no_cors_headers_by_default(self, client):
        response = client.get("/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in response.headers
        preflight = client.options("/users/me/lists", headers={
            "Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in preflight.headers


class TestPasswordHashes:
    def test_hashes_from_earlier_versions_still_verify(self):
        assert verify_password("testpassword", PASSLIB_HASH)
        assert not verify_password("wrongpassword", PASSLIB_HASH)
        assert verify_password("p" * 80, PASSLIB_LONG_HASH)
        assert verify_password("p" * 72, PASSLIB_LONG_HASH)

    def test_new_hashes(self):
        hashed = get_password_hash("correct horse")
        assert hashed.startswith("$2b$")
        assert verify_password("correct horse", hashed)
        assert not verify_password("correct horsE", hashed)
        assert verify_password("é" * 50, get_password_hash("é" * 50))

    def test_a_value_that_is_not_a_hash_never_verifies(self):
        assert not verify_password("anything", "not-a-bcrypt-hash")


class TestTokens:
    def _get(self, client, token):
        return client.get("/users/me/lists", headers={"Authorization": f"Bearer {token}"})

    def test_token_signed_with_the_old_placeholder_is_rejected(self, client, test_user):
        forged = jwt.encode({"sub": "testuser", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                            "your-secret-key-change-this-in-production", algorithm="HS256")
        assert self._get(client, forged).status_code == status.HTTP_401_UNAUTHORIZED

    def test_unsigned_token_is_rejected(self, client, test_user):
        unsigned = jwt.encode({"sub": "testuser", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, None, algorithm="none")
        assert self._get(client, unsigned).status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_without_expiry_is_rejected(self, client, test_user):
        token = jwt.encode({"sub": "testuser"}, settings.secret_key, algorithm=settings.algorithm)
        assert self._get(client, token).status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_is_rejected(self, client, test_user):
        token = jwt.encode({"sub": "testuser", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                           settings.secret_key, algorithm=settings.algorithm)
        assert self._get(client, token).status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_token_is_accepted(self, client, test_user):
        login = client.post("/auth/login", data={"username": "testuser", "password": "testpassword"})
        assert login.status_code == status.HTTP_200_OK
        assert self._get(client, login.json()["access_token"]).status_code == status.HTTP_200_OK


class TestManageCommand:
    @pytest.fixture(autouse=True)
    def use_test_database(self, monkeypatch, db_session):
        monkeypatch.setattr(manage, "SessionLocal", TestingSessionLocal)
        monkeypatch.setattr(manage, "engine", engine)
        self.db_session = db_session

    def run(self, monkeypatch, *args, stdin=""):
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
        try:
            return manage.main(list(args))
        finally:
            # The API's test session caches users; the command changed them
            # in its own session, as it would in another process
            self.db_session.expire_all()

    def test_create_user_then_log_in(self, client, monkeypatch, capsys):
        assert self.run(monkeypatch, "create-user", "alice", "Alice@Example.com", "--password-stdin", stdin="s3cret-pass\n") == 0
        assert "Created user alice" in capsys.readouterr().out
        login = client.post("/auth/login", data={"username": "alice", "password": "s3cret-pass"})
        assert login.status_code == status.HTTP_200_OK

    def test_create_user_refuses_duplicates_and_short_passwords(self, monkeypatch):
        self.run(monkeypatch, "create-user", "alice", "a@example.com", "--password-stdin", stdin="s3cret-pass\n")
        with pytest.raises(SystemExit, match="taken"):
            self.run(monkeypatch, "create-user", "alice", "b@example.com", "--password-stdin", stdin="s3cret-pass\n")
        with pytest.raises(SystemExit, match="already used"):
            self.run(monkeypatch, "create-user", "bob", "a@example.com", "--password-stdin", stdin="s3cret-pass\n")
        with pytest.raises(SystemExit, match="at least"):
            self.run(monkeypatch, "create-user", "carol", "c@example.com", "--password-stdin", stdin="short\n")
        with pytest.raises(SystemExit, match="Invalid email"):
            self.run(monkeypatch, "create-user", "dave", "not-an-email", "--password-stdin", stdin="s3cret-pass\n")

    def test_set_password_and_deactivate(self, client, monkeypatch, test_user):
        self.run(monkeypatch, "set-password", "testuser", "--password-stdin", stdin="new-password\n")
        assert client.post("/auth/login", data={"username": "testuser", "password": "testpassword"}).status_code == 401
        assert client.post("/auth/login", data={"username": "testuser", "password": "new-password"}).status_code == 200

        self.run(monkeypatch, "deactivate-user", "testuser")
        assert client.post("/auth/login", data={"username": "testuser", "password": "new-password"}).status_code != 200
        self.run(monkeypatch, "activate-user", "testuser")
        assert client.post("/auth/login", data={"username": "testuser", "password": "new-password"}).status_code == 200

    def test_list_users(self, monkeypatch, capsys, test_user):
        self.run(monkeypatch, "list-users")
        assert "testuser\ttest@example.com\tactive" in capsys.readouterr().out

    def test_unknown_user(self, monkeypatch):
        with pytest.raises(SystemExit, match="No user"):
            self.run(monkeypatch, "set-password", "nobody", "--password-stdin", stdin="new-password\n")
