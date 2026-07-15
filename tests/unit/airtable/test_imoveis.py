from unittest.mock import MagicMock, patch

from crmToVoice.airtable import imoveis


def test_create_imovel_passes_fields_through():
    fake_table = MagicMock()
    fake_table.create.return_value = {"id": "recNew", "fields": {"Morada": "Rua X"}}

    with patch.object(imoveis, "get_table", return_value=fake_table) as mock_get_table:
        result = imoveis.create_imovel({"Morada": "Rua X"})

    mock_get_table.assert_called_once_with("Imóveis")
    fake_table.create.assert_called_once_with({"Morada": "Rua X"})
    assert result == {"id": "recNew", "fields": {"Morada": "Rua X"}}


def test_update_imovel_passes_record_id_and_fields_through():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "rec1", "fields": {"Preço": 250000}}

    with patch.object(imoveis, "get_table", return_value=fake_table):
        result = imoveis.update_imovel("rec1", {"Preço": 250000})

    fake_table.update.assert_called_once_with("rec1", {"Preço": 250000})
    assert result == {"id": "rec1", "fields": {"Preço": 250000}}


def test_update_imovel_allows_updating_estado():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "rec1", "fields": {"Estado": "Reservado"}}

    with patch.object(imoveis, "get_table", return_value=fake_table):
        result = imoveis.update_imovel("rec1", {"Estado": "Reservado"})

    fake_table.update.assert_called_once_with("rec1", {"Estado": "Reservado"})
    assert result == {"id": "rec1", "fields": {"Estado": "Reservado"}}


def test_delete_imovel_calls_table_delete():
    fake_table = MagicMock()

    with patch.object(imoveis, "get_table", return_value=fake_table):
        imoveis.delete_imovel("rec1")

    fake_table.delete.assert_called_once_with("rec1")


def test_search_imoveis_builds_case_insensitive_formula_and_returns_matches():
    fake_table = MagicMock()
    fake_table.all.return_value = [{"id": "rec1", "fields": {"Morada": "Rua das Flores"}}]

    with patch.object(imoveis, "get_table", return_value=fake_table):
        result = imoveis.search_imoveis("flores")

    assert fake_table.all.call_count == 1
    _, kwargs = fake_table.all.call_args
    assert "formula" in kwargs
    assert "SEARCH" in kwargs["formula"]
    assert "Morada" in kwargs["formula"]
    assert result == [{"id": "rec1", "fields": {"Morada": "Rua das Flores"}}]


def test_get_imovel_expands_linked_visitas():
    fake_table = MagicMock()
    fake_table.get.return_value = {
        "id": "rec1",
        "fields": {"Morada": "Rua X", "Visitas": ["recV1", "recV2"]},
    }
    fake_visitas = [{"id": "recV1", "fields": {}}, {"id": "recV2", "fields": {}}]

    with (
        patch.object(imoveis, "get_table", return_value=fake_table),
        patch.object(imoveis, "get_records_by_ids", return_value=fake_visitas) as mock_grbi,
    ):
        result = imoveis.get_imovel("rec1")

    mock_grbi.assert_called_once_with("Visitas", ["recV1", "recV2"])
    assert result["visitas"] == fake_visitas
    assert result["fields"]["Visitas"] == ["recV1", "recV2"]


def test_get_imovel_with_no_linked_visitas_returns_empty_list():
    fake_table = MagicMock()
    fake_table.get.return_value = {"id": "rec1", "fields": {"Morada": "Rua X"}}

    with (
        patch.object(imoveis, "get_table", return_value=fake_table),
        patch.object(imoveis, "get_records_by_ids", return_value=[]) as mock_grbi,
    ):
        result = imoveis.get_imovel("rec1")

    mock_grbi.assert_called_once_with("Visitas", [])
    assert result["visitas"] == []
