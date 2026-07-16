from unittest.mock import patch

import pytest
from pydantic import SecretStr

from crmToVoice import config


@pytest.fixture(autouse=True)
def _reset_chat_model_cache():
    config.get_chat_model.cache_clear()
    yield
    config.get_chat_model.cache_clear()


def test_get_openrouter_model_reads_env_var(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    assert config.get_openrouter_model() == "openai/gpt-4o-mini"


def test_get_openrouter_model_raises_if_missing(monkeypatch):
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    with pytest.raises(KeyError):
        config.get_openrouter_model()


def test_get_chat_model_builds_client_from_env_vars(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    with patch.object(config, "ChatOpenAI") as mock_chat_openai_cls:
        config.get_chat_model()

    mock_chat_openai_cls.assert_called_once_with(
        model="openai/gpt-4o-mini",
        api_key=SecretStr("fake-key"),
        base_url=config.OPENROUTER_BASE_URL,
    )


def test_get_chat_model_is_cached_across_calls(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    with patch.object(config, "ChatOpenAI") as mock_chat_openai_cls:
        first = config.get_chat_model()
        second = config.get_chat_model()

    assert first is second
    mock_chat_openai_cls.assert_called_once()


def test_get_chat_model_raises_if_api_key_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(KeyError):
        config.get_chat_model()
