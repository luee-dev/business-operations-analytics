from unittest.mock import MagicMock

import pytest

from boa.config import database


@pytest.fixture(autouse=True)
def clear_engine_cache():
    database.get_engine.cache_clear()
    yield
    database.get_engine.cache_clear()


def test_get_database_url():
    url = database.get_database_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.username == database.settings.POSTGRES_USER
    assert url.password == database.settings.POSTGRES_PASSWORD
    assert url.host == database.settings.POSTGRES_HOST
    assert url.port == database.settings.POSTGRES_PORT
    assert url.database == database.settings.POSTGRES_DB


def test_get_database_url_uses_current_settings(monkeypatch):
    monkeypatch.setattr(database.settings, "POSTGRES_HOST", "test-host")
    monkeypatch.setattr(database.settings, "POSTGRES_PORT", 6543)
    monkeypatch.setattr(database.settings, "POSTGRES_DB", "test_db")
    monkeypatch.setattr(database.settings, "POSTGRES_USER", "test_user")
    monkeypatch.setattr(database.settings, "POSTGRES_PASSWORD", "test_pass")

    url = database.get_database_url()

    assert url.host == "test-host"
    assert url.port == 6543
    assert url.database == "test_db"
    assert url.username == "test_user"
    assert url.password == "test_pass"


def test_get_engine_creates_engine_with_pre_ping(monkeypatch):
    mock_engine = MagicMock()

    create_engine = MagicMock(return_value=mock_engine)

    monkeypatch.setattr(database, "create_engine", create_engine)

    result = database.get_engine()

    assert result is mock_engine

    create_engine.assert_called_once()

    args, kwargs = create_engine.call_args

    assert args[0] == database.get_database_url()
    assert kwargs["pool_pre_ping"] is True


def test_get_engine_caches_engine(monkeypatch):
    mock_engine = MagicMock()

    create_engine = MagicMock(return_value=mock_engine)

    monkeypatch.setattr(database, "create_engine", create_engine)

    first_engine = database.get_engine()
    second_engine = database.get_engine()

    assert first_engine is second_engine
    create_engine.assert_called_once()


def test_test_connection_returns_true(monkeypatch):
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar_one.return_value = 1

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    monkeypatch.setattr(database, "get_engine", lambda: mock_engine)

    result = database.test_connection()

    assert result is True
    mock_connection.execute.assert_called_once()


def test_test_connection_returns_false_for_unexpected_result(
    monkeypatch,
):
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar_one.return_value = 0

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    monkeypatch.setattr(database, "get_engine", lambda: mock_engine)

    assert database.test_connection() is False


def test_test_connection_propagates_connection_errors(monkeypatch):
    mock_engine = MagicMock()

    mock_engine.connect.side_effect = RuntimeError("Database unavailable")

    monkeypatch.setattr(database, "get_engine", lambda: mock_engine)

    with pytest.raises(RuntimeError, match="Database unavailable"):
        database.test_connection()
