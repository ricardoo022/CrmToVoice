from unittest.mock import MagicMock, patch

import pytest

from crmToVoice.airtable import client


@pytest.fixture(autouse=True)
def _reset_api_cache():
    client.get_api.cache_clear()
    yield
    client.get_api.cache_clear()


def test_get_api_builds_client_from_env_var(monkeypatch):
    monkeypatch.setenv("AIRTABLE_API_KEY", "fake-key")
    with patch.object(client, "Api") as mock_api_cls:
        client.get_api()
        mock_api_cls.assert_called_once_with("fake-key")


def test_get_api_is_cached_across_calls(monkeypatch):
    monkeypatch.setenv("AIRTABLE_API_KEY", "fake-key")
    with patch.object(client, "Api") as mock_api_cls:
        first = client.get_api()
        second = client.get_api()
        assert first is second
        mock_api_cls.assert_called_once()


def test_get_api_raises_if_api_key_missing(monkeypatch):
    monkeypatch.delenv("AIRTABLE_API_KEY", raising=False)
    with pytest.raises(KeyError):
        client.get_api()


def test_get_table_uses_base_id_env_var_and_table_name(monkeypatch):
    monkeypatch.setenv("AIRTABLE_BASE_ID", "appFakeBase12345")
    fake_table = MagicMock()
    fake_api = MagicMock()
    fake_api.table.return_value = fake_table

    with patch.object(client, "get_api", return_value=fake_api):
        result = client.get_table("Leads")

    fake_api.table.assert_called_once_with("appFakeBase12345", "Leads")
    assert result is fake_table


def test_get_records_by_ids_fetches_each_record():
    fake_table = MagicMock()
    fake_table.get.side_effect = lambda rid: {"id": rid, "fields": {}}

    with patch.object(client, "get_table", return_value=fake_table) as mock_get_table:
        result = client.get_records_by_ids("Visitas", ["rec1", "rec2"])

    mock_get_table.assert_called_once_with("Visitas")
    assert result == [{"id": "rec1", "fields": {}}, {"id": "rec2", "fields": {}}]


def test_get_records_by_ids_empty_list_returns_empty():
    with patch.object(client, "get_table") as mock_get_table:
        mock_get_table.return_value = MagicMock()
        result = client.get_records_by_ids("Visitas", [])

    assert result == []
