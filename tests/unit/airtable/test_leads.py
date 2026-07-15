from unittest.mock import MagicMock, patch

from crmToVoice.airtable import leads


def test_create_lead_passes_fields_through():
    fake_table = MagicMock()
    fake_table.create.return_value = {"id": "recNew", "fields": {"Nome": "Maria"}}

    with patch.object(leads, "get_table", return_value=fake_table) as mock_get_table:
        result = leads.create_lead({"Nome": "Maria"})

    mock_get_table.assert_called_once_with("Leads")
    fake_table.create.assert_called_once_with({"Nome": "Maria"})
    assert result == {"id": "recNew", "fields": {"Nome": "Maria"}}


def test_update_lead_passes_record_id_and_fields_through():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "rec1", "fields": {"Estado": "Contactado"}}

    with patch.object(leads, "get_table", return_value=fake_table):
        result = leads.update_lead("rec1", {"Estado": "Contactado"})

    fake_table.update.assert_called_once_with("rec1", {"Estado": "Contactado"})
    assert result == {"id": "rec1", "fields": {"Estado": "Contactado"}}


def test_update_lead_allows_automatic_field_like_sentimento():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "rec1", "fields": {"Sentimento": "Positivo"}}

    with patch.object(leads, "get_table", return_value=fake_table):
        result = leads.update_lead("rec1", {"Sentimento": "Positivo"})

    fake_table.update.assert_called_once_with("rec1", {"Sentimento": "Positivo"})
    assert result == {"id": "rec1", "fields": {"Sentimento": "Positivo"}}


def test_update_lead_allows_automatic_field_like_estado():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "rec1", "fields": {"Estado": "Qualificado"}}

    with patch.object(leads, "get_table", return_value=fake_table):
        result = leads.update_lead("rec1", {"Estado": "Qualificado"})

    fake_table.update.assert_called_once_with("rec1", {"Estado": "Qualificado"})
    assert result == {"id": "rec1", "fields": {"Estado": "Qualificado"}}


def test_update_lead_allows_automatic_field_like_data_ultima_interacao():
    fake_table = MagicMock()
    fake_table.update.return_value = {
        "id": "rec1",
        "fields": {"Data Última Interação": "2026-07-15"},
    }

    with patch.object(leads, "get_table", return_value=fake_table):
        result = leads.update_lead("rec1", {"Data Última Interação": "2026-07-15"})

    fake_table.update.assert_called_once_with("rec1", {"Data Última Interação": "2026-07-15"})
    assert result == {"id": "rec1", "fields": {"Data Última Interação": "2026-07-15"}}


def test_delete_lead_calls_table_delete():
    fake_table = MagicMock()

    with patch.object(leads, "get_table", return_value=fake_table):
        leads.delete_lead("rec1")

    fake_table.delete.assert_called_once_with("rec1")


def test_search_leads_builds_case_insensitive_formula_and_returns_matches():
    fake_table = MagicMock()
    fake_table.all.return_value = [{"id": "rec1", "fields": {"Nome": "João Silva"}}]

    with patch.object(leads, "get_table", return_value=fake_table):
        result = leads.search_leads("joão")

    assert fake_table.all.call_count == 1
    _, kwargs = fake_table.all.call_args
    assert "formula" in kwargs
    assert "SEARCH" in kwargs["formula"]
    assert "Nome" in kwargs["formula"]
    assert result == [{"id": "rec1", "fields": {"Nome": "João Silva"}}]


def test_get_lead_expands_linked_visitas():
    fake_table = MagicMock()
    fake_table.get.return_value = {
        "id": "rec1",
        "fields": {"Nome": "João", "Visitas": ["recV1", "recV2"]},
    }
    fake_visitas = [{"id": "recV1", "fields": {}}, {"id": "recV2", "fields": {}}]

    with (
        patch.object(leads, "get_table", return_value=fake_table),
        patch.object(leads, "get_records_by_ids", return_value=fake_visitas) as mock_grbi,
    ):
        result = leads.get_lead("rec1")

    mock_grbi.assert_called_once_with("Visitas", ["recV1", "recV2"])
    assert result["visitas"] == fake_visitas
    assert result["fields"]["Visitas"] == ["recV1", "recV2"]


def test_get_lead_with_no_linked_visitas_returns_empty_list():
    fake_table = MagicMock()
    fake_table.get.return_value = {"id": "rec1", "fields": {"Nome": "João"}}

    with (
        patch.object(leads, "get_table", return_value=fake_table),
        patch.object(leads, "get_records_by_ids", return_value=[]) as mock_grbi,
    ):
        result = leads.get_lead("rec1")

    mock_grbi.assert_called_once_with("Visitas", [])
    assert result["visitas"] == []
