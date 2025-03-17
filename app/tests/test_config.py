import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest import ExceptionInfo

from app.config import check_env


def test_check_env_ok(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FIREBLOCKS_API_KEY", "some_key")
    monkeypatch.setenv("RABBITMQ_URL", "amqp://localhost:5672/")
    # If needed, also mock presence of the private key file or skip
    check_env()  # should not raise


def test_check_env_missing(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("FIREBLOCKS_API_KEY", raising=False)
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    with pytest.raises(EnvironmentError) as exc:
        check_env()
    # Checking the exception message
    assert "Missing required env vars: ['FIREBLOCKS_API_KEY', 'RABBITMQ_URL']" in str(exc.value)
