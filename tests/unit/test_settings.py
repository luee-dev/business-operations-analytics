import pytest
from pydantic import ValidationError

from boa.config.settings import Settings


def test_settings_load_default_values():
    settings = Settings(
        _env_file=None,
        POSTGRES_PASSWORD="test_password",
    )

    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == 5432
    assert settings.POSTGRES_DB == "business_analytics"
    assert settings.POSTGRES_USER == "boa_user"
    assert settings.POSTGRES_PASSWORD == "test_password"


def test_settings_load_custom_values():
    settings = Settings(
        _env_file=None,
        POSTGRES_HOST="test-host",
        POSTGRES_PORT=6543,
        POSTGRES_DB="test_database",
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
    )

    assert settings.POSTGRES_HOST == "test-host"
    assert settings.POSTGRES_PORT == 6543
    assert settings.POSTGRES_DB == "test_database"
    assert settings.POSTGRES_USER == "test_user"
    assert settings.POSTGRES_PASSWORD == "test_password"


def test_settings_read_environment_variables(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "environment-host")
    monkeypatch.setenv("POSTGRES_PORT", "7654")
    monkeypatch.setenv("POSTGRES_DB", "environment_db")
    monkeypatch.setenv("POSTGRES_USER", "environment_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "environment_password")

    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "environment-host"
    assert settings.POSTGRES_PORT == 7654
    assert settings.POSTGRES_DB == "environment_db"
    assert settings.POSTGRES_USER == "environment_user"
    assert settings.POSTGRES_PASSWORD == "environment_password"


def test_settings_read_env_file(tmp_path):
    env_file = tmp_path / ".env"

    env_file.write_text(
        (
            "POSTGRES_HOST=file-host\n"
            "POSTGRES_PORT=8765\n"
            "POSTGRES_DB=file_database\n"
            "POSTGRES_USER=file_user\n"
            "POSTGRES_PASSWORD=file_password\n"
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.POSTGRES_HOST == "file-host"
    assert settings.POSTGRES_PORT == 8765
    assert settings.POSTGRES_DB == "file_database"
    assert settings.POSTGRES_USER == "file_user"
    assert settings.POSTGRES_PASSWORD == "file_password"


def test_settings_requires_database_password():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
