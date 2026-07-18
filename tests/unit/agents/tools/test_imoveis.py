from unittest.mock import patch

from crmToVoice.agents.tools import imoveis
from crmToVoice.airtable import imoveis as airtable_imoveis


def test_create_imovel_calls_airtable_and_returns_result():
    mock_result = {"id": "recNew", "fields": {"Morada": "Rua X"}}

    with patch.object(airtable_imoveis, "create_imovel", return_value=mock_result) as mock_fn:
        result = imoveis.create_imovel.invoke({"fields": {"Morada": "Rua X"}})

    mock_fn.assert_called_once_with({"Morada": "Rua X"})
    assert result == mock_result


def test_update_imovel_calls_airtable_and_returns_result():
    mock_result = {"id": "rec1", "fields": {"Preço": 250000}}

    with patch.object(airtable_imoveis, "update_imovel", return_value=mock_result) as mock_fn:
        result = imoveis.update_imovel.invoke({"record_id": "rec1", "fields": {"Preço": 250000}})

    mock_fn.assert_called_once_with("rec1", {"Preço": 250000})
    assert result == mock_result


def test_delete_imovel_calls_airtable():
    with patch.object(airtable_imoveis, "delete_imovel", return_value=None) as mock_fn:
        result = imoveis.delete_imovel.invoke({"record_id": "rec1"})

    mock_fn.assert_called_once_with("rec1")
    assert result is None


def test_search_imoveis_calls_airtable_and_returns_result():
    mock_result = [{"id": "rec1", "fields": {"Morada": "Rua das Flores"}}]

    with patch.object(airtable_imoveis, "search_imoveis", return_value=mock_result) as mock_fn:
        result = imoveis.search_imoveis.invoke({"morada": "flores"})

    mock_fn.assert_called_once_with("flores")
    assert result == mock_result


def test_get_imovel_calls_airtable_and_returns_result():
    mock_result = {
        "id": "rec1",
        "fields": {"Morada": "Rua X"},
        "visitas": [{"id": "recV1", "fields": {}}],
    }

    with patch.object(airtable_imoveis, "get_imovel", return_value=mock_result) as mock_fn:
        result = imoveis.get_imovel.invoke({"record_id": "rec1"})

    mock_fn.assert_called_once_with("rec1")
    assert result == mock_result


def test_search_imoveis_returns_empty_list_when_no_matches():
    with patch.object(airtable_imoveis, "search_imoveis", return_value=[]) as mock_fn:
        result = imoveis.search_imoveis.invoke({"morada": "inexistente"})

    mock_fn.assert_called_once_with("inexistente")
    assert result == []


def test_get_imovel_passes_through_record_with_empty_visitas():
    mock_result = {"id": "rec1", "fields": {"Morada": "Rua X"}, "visitas": []}

    with patch.object(airtable_imoveis, "get_imovel", return_value=mock_result) as mock_fn:
        result = imoveis.get_imovel.invoke({"record_id": "rec1"})

    mock_fn.assert_called_once_with("rec1")
    assert result == mock_result
    assert result["visitas"] == []


# --- find_imovel (composite tool) ---


def test_find_imovel_returns_full_record_with_visitas_when_found():
    """find_imovel should search, then get the full record including visitas."""
    search_result = [{"id": "rec1", "fields": {"Morada": "Rua das Flores"}}]
    full_imovel = {
        "id": "rec1",
        "fields": {"Morada": "Rua das Flores", "Visitas": ["recV1"]},
        "visitas": [{"id": "recV1", "fields": {"Título": "Visita 1"}}],
    }

    with (
        patch.object(airtable_imoveis, "search_imoveis", return_value=search_result),
        patch.object(airtable_imoveis, "get_imovel", return_value=full_imovel) as mock_get,
    ):
        result = imoveis.find_imovel.invoke({"morada": "flores"})

    mock_get.assert_called_once_with("rec1")
    assert result["found"] is True
    assert result["id"] == "rec1"
    assert result["visitas"] == full_imovel["visitas"]


def test_find_imovel_returns_not_found_when_search_empty():
    """find_imovel should return found=False when no match."""
    with (
        patch.object(airtable_imoveis, "search_imoveis", return_value=[]),
        patch.object(airtable_imoveis, "get_imovel") as mock_get,
    ):
        result = imoveis.find_imovel.invoke({"morada": "inexistente"})

    mock_get.assert_not_called()
    assert result["found"] is False
    assert result["imovel"] is None
    assert result["visitas"] == []


def test_find_imovel_uses_first_match_when_multiple_found():
    """find_imovel should use the first match when search returns multiple."""
    search_result = [
        {"id": "rec1", "fields": {"Morada": "Rua A"}},
        {"id": "rec2", "fields": {"Morada": "Rua A Bis"}},
    ]
    full_imovel = {"id": "rec1", "fields": {"Morada": "Rua A"}, "visitas": []}

    with (
        patch.object(airtable_imoveis, "search_imoveis", return_value=search_result),
        patch.object(airtable_imoveis, "get_imovel", return_value=full_imovel) as mock_get,
    ):
        result = imoveis.find_imovel.invoke({"morada": "rua"})

    mock_get.assert_called_once_with("rec1")
    assert result["found"] is True
