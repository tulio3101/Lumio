import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_SECRET = "a" * 64


@pytest.mark.parametrize("environment", ["dev", "prod"])
def test_rejects_default_jwt_secret_outside_local(environment):
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment=environment, jwt_secret="change-me", _env_file=None)


def test_rejects_short_jwt_secret_outside_local():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="dev", jwt_secret="corto", _env_file=None)


def test_accepts_strong_jwt_secret_outside_local():
    settings = Settings(environment="dev", jwt_secret=STRONG_SECRET, _env_file=None)

    assert settings.jwt_secret == STRONG_SECRET


def test_local_keeps_default_secret_for_development():
    settings = Settings(environment="local", jwt_secret="change-me", _env_file=None)

    assert settings.environment == "local"