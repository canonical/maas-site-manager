from datetime import timedelta
import hashlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from msm.apiserver.service.token import OIDCRevokedTokenService, TokenService
from msm.common.jwt import (
    JWT,
    TokenAudience,
    TokenPurpose,
)
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestTokenService:
    async def test_create(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        duration = timedelta(minutes=10)
        service = TokenService(db_connection)
        tokens = list(
            await service.create(
                issuer="issuer",
                duration=duration,
                count=10,
            )
        )
        assert len(tokens) == 10
        for token in tokens:
            assert token.expired - token.created == duration
        db_tokens = await factory.get("token")
        assert {token.value for token in tokens} == {
            token["value"] for token in db_tokens
        }

    async def test_create_value_is_jwt(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        issuer = "issuer"
        secret_key = "abcde"
        duration = timedelta(minutes=10)
        service = TokenService(db_connection)
        [token] = await service.create(
            issuer=issuer, duration=duration, secret_key=secret_key
        )
        decoded_token = JWT.decode(
            token.value,
            key=secret_key,
            issuer=issuer,
            audience=TokenAudience.SITE,
            purpose=TokenPurpose.ENROLMENT,
        )
        [db_token] = await factory.get("token")
        assert db_token["auth_id"] == uuid.UUID(decoded_token.subject)

    async def test_get_includes_only_active(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2, uuid3 = (uuid.uuid4() for _ in range(3))
        await factory.make_Token(auth_id=uuid1, lifetime=timedelta(hours=-1))
        await factory.make_Token(auth_id=uuid2, lifetime=timedelta(hours=1))
        await factory.make_Token(auth_id=uuid3, lifetime=timedelta(hours=2))

        service = TokenService(db_connection)
        count, tokens = await service.get()
        assert count == 2
        assert {
            JWT.decode(
                token.value,
                issuer="issuer",
                audience=TokenAudience.SITE,
            ).subject
            for token in tokens
        } == {
            str(uuid2),
            str(uuid3),
        }

    async def test_get_includes_only_unused(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2 = (uuid.uuid4() for _ in range(2))
        await factory.make_Site(auth_id=uuid1)
        await factory.make_Token(auth_id=uuid2, lifetime=timedelta(hours=1))

        service = TokenService(db_connection)
        count, tokens = await service.get()
        assert count == 1
        assert {
            JWT.decode(
                token.value,
                issuer="issuer",
                audience=TokenAudience.SITE,
            ).subject
            for token in tokens
        } == {
            str(uuid2),
        }

    async def test_get_by_auth_id(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2, uuid3 = (uuid.uuid4() for _ in range(3))
        await factory.make_Token(auth_id=uuid1, lifetime=timedelta(hours=-1))
        await factory.make_Token(auth_id=uuid2, lifetime=timedelta(hours=1))
        service = TokenService(db_connection)
        assert await service.get_by_auth_id(uuid1) is not None
        assert await service.get_by_auth_id(uuid2) is not None
        assert await service.get_by_auth_id(uuid3) is None

    async def test_delete(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        duration = timedelta(minutes=10)
        service = TokenService(db_connection)
        tokens = list(
            await service.create(
                issuer="issuer",
                duration=duration,
                count=10,
            )
        )
        await service.delete(tokens[0].id)
        db_tokens = await factory.get("token")
        assert len(db_tokens) == 9
        assert tokens[0].value not in {token["value"] for token in db_tokens}

    async def test_delete_many(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        duration = timedelta(minutes=10)
        service = TokenService(db_connection)
        tokens = list(
            await service.create(
                issuer="issuer",
                duration=duration,
                count=10,
            )
        )
        await service.delete_many([tokens[0].id, tokens[1].id])
        db_tokens = await factory.get("token")
        assert len(db_tokens) == 8
        assert tokens[0].value not in {token["value"] for token in db_tokens}
        assert tokens[1].value not in {token["value"] for token in db_tokens}

    async def test_get_worker_token(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uid = uuid.uuid4()
        await factory.make_Token(
            auth_id=uid,
            lifetime=timedelta(hours=1),
            audience=TokenAudience.WORKER,
            purpose=TokenPurpose.ACCESS,
        )

        service = TokenService(db_connection)
        count, tokens = await service.get(
            audience=[TokenAudience.WORKER], purpose=[TokenPurpose.ACCESS]
        )
        assert count == 1
        token = next(iter(tokens))
        assert JWT.decode(
            token.value,
            issuer="issuer",
            audience=TokenAudience.WORKER,
        ).subject == str(uid)

    async def test_delete_expired(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2, uuid3 = (uuid.uuid4() for _ in range(3))
        await factory.make_Token(auth_id=uuid1, lifetime=timedelta(hours=-2))
        await factory.make_Token(auth_id=uuid2, lifetime=timedelta(hours=-1))
        await factory.make_Token(auth_id=uuid3, lifetime=timedelta(hours=1))

        service = TokenService(db_connection)
        deleted = await service.delete_expired()
        assert deleted == 2
        db_tokens = await factory.get("token")
        assert len(db_tokens) == 1

    async def test_delete_expired_filters_by_audience(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2 = (uuid.uuid4() for _ in range(2))
        await factory.make_Token(
            auth_id=uuid1,
            lifetime=timedelta(hours=-1),
            audience=TokenAudience.WORKER,
            purpose=TokenPurpose.ACCESS,
        )
        await factory.make_Token(
            auth_id=uuid2,
            lifetime=timedelta(hours=-1),
            audience=TokenAudience.SITE,
        )

        service = TokenService(db_connection)
        deleted = await service.delete_expired(audience=TokenAudience.WORKER)
        assert deleted == 1
        # SITE token should still be in the database
        db_tokens = await factory.get("token")
        assert len(db_tokens) == 1

    async def test_delete_expired_filters_by_purpose(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        uuid1, uuid2 = (uuid.uuid4() for _ in range(2))
        await factory.make_Token(
            auth_id=uuid1,
            lifetime=timedelta(hours=-1),
            audience=TokenAudience.WORKER,
            purpose=TokenPurpose.ACCESS,
        )
        await factory.make_Token(
            auth_id=uuid2,
            lifetime=timedelta(hours=-1),
            audience=TokenAudience.SITE,
            purpose=TokenPurpose.ENROLMENT,
        )

        service = TokenService(db_connection)
        deleted = await service.delete_expired(purpose=TokenPurpose.ENROLMENT)
        assert deleted == 1
        # SITE token should still be in the database
        db_tokens = await factory.get("token")
        assert len(db_tokens) == 1


# Helpers shared across OIDCRevokedTokenService tests
_METADATA = {
    "authorization_endpoint": "https://issuer.com/authorize",
    "token_endpoint": "https://issuer.com/token",
    "jwks_uri": "https://issuer.com/jwks",
}

# OIDC users have username == email in this project.
_OIDC_EMAIL = "oidcuser@example.com"


async def _insert_provider(factory: Factory) -> int:
    """Insert a minimal OIDC provider and return its id."""
    await factory.create(
        "oidc_provider",
        [
            {
                "name": "test-provider",
                "client_id": "client",
                "client_secret": "secret",
                "issuer_url": "https://issuer.com/",
                "redirect_uri": "https://example.com/callback",
                "scopes": "openid",
                "token_type": "OPAQUE",
                "enabled": True,
                "metadata": _METADATA,
            }
        ],
    )
    [row] = await factory.get("oidc_provider")
    return int(row["id"])


async def _insert_oidc_user(factory: Factory) -> None:
    """Insert an OIDC user whose username equals their email (project convention)."""
    await factory.make_User(username=_OIDC_EMAIL, email=_OIDC_EMAIL)


@pytest.mark.asyncio
class TestOIDCRevokedTokenService:
    async def test_create_revoked_token_stores_hash(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """Raw token must never be stored; only its SHA-256 hash."""
        provider_id = await _insert_provider(factory)
        await _insert_oidc_user(factory)
        raw_token = "super-secret-refresh-token"

        service = OIDCRevokedTokenService(db_connection)
        result = await service.create_revoked_token(
            token=raw_token,
            provider_id=provider_id,
            email=_OIDC_EMAIL,
        )

        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        assert result.token_hash == expected_hash
        assert result.token_hash != raw_token
        assert result.provider_id == provider_id
        assert result.user_email == _OIDC_EMAIL

    async def test_create_revoked_token_persisted(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """Created row must be visible in the database."""
        provider_id = await _insert_provider(factory)
        await _insert_oidc_user(factory)

        service = OIDCRevokedTokenService(db_connection)
        await service.create_revoked_token(
            token="my-token",
            provider_id=provider_id,
            email=_OIDC_EMAIL,
        )

        rows = await factory.get("oidc_revoked_token")
        assert len(rows) == 1
        assert rows[0]["token_hash"] == hashlib.sha256(b"my-token").hexdigest()

    async def test_is_revoked_true(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """A token whose hash is in the denylist must be reported as revoked."""
        provider_id = await _insert_provider(factory)
        await _insert_oidc_user(factory)
        raw_token = "revoked-token"

        service = OIDCRevokedTokenService(db_connection)
        await service.create_revoked_token(
            token=raw_token,
            provider_id=provider_id,
            email=_OIDC_EMAIL,
        )

        assert await service.is_revoked(raw_token) is True

    async def test_is_revoked_false(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """A token not in the denylist must not be reported as revoked."""
        service = OIDCRevokedTokenService(db_connection)
        assert await service.is_revoked("unknown-token") is False

    async def test_is_revoked_different_token(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """A different token must not be considered revoked even if another is."""
        provider_id = await _insert_provider(factory)
        await _insert_oidc_user(factory)

        service = OIDCRevokedTokenService(db_connection)
        await service.create_revoked_token(
            token="revoked-token",
            provider_id=provider_id,
            email=_OIDC_EMAIL,
        )

        assert await service.is_revoked("other-token") is False

    async def test_make_oidc_revoked_token_factory(
        self, factory: Factory, db_connection: AsyncConnection
    ) -> None:
        """Factory helper must insert a row and return a valid model."""
        provider_id = await _insert_provider(factory)
        await _insert_oidc_user(factory)

        token = await factory.make_OIDCRevokedToken(
            user_email=_OIDC_EMAIL, provider_id=provider_id
        )

        assert token.id is not None
        assert token.provider_id == provider_id
        assert token.user_email == _OIDC_EMAIL
        rows = await factory.get("oidc_revoked_token")
        assert len(rows) == 1
