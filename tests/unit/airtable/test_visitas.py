from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from pyairtable.formulas import AND, IS_AFTER, IS_BEFORE, Field
from pyairtable.utils import datetime_to_iso_str

from crmToVoice.airtable import visitas


def test_create_visita_creates_record_when_lead_present():
    fake_table = MagicMock()
    fake_table.create.return_value = {"id": "recVisita1", "fields": {"Lead": ["recLead1"]}}

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.create_visita({"Resumo": "Correu bem", "Lead": ["recLead1"]})

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.create.assert_called_once_with({"Resumo": "Correu bem", "Lead": ["recLead1"]})
    assert result == {"id": "recVisita1", "fields": {"Lead": ["recLead1"]}}


def test_create_visita_creates_record_with_lead_and_imovel():
    fake_table = MagicMock()
    fake_table.create.return_value = {
        "id": "recVisita2",
        "fields": {"Lead": ["recLead1"], "Imóvel": ["recImovel1"]},
    }

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.create_visita(
            {"Resumo": "Visitou o apartamento", "Lead": ["recLead1"], "Imóvel": ["recImovel1"]}
        )

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.create.assert_called_once_with(
        {"Resumo": "Visitou o apartamento", "Lead": ["recLead1"], "Imóvel": ["recImovel1"]}
    )
    assert result == {
        "id": "recVisita2",
        "fields": {"Lead": ["recLead1"], "Imóvel": ["recImovel1"]},
    }


def test_create_visita_raises_when_lead_key_missing():
    with pytest.raises(ValueError, match="Lead"):
        visitas.create_visita({"Resumo": "Sem lead"})


def test_create_visita_raises_when_lead_empty_list():
    with pytest.raises(ValueError, match="Lead"):
        visitas.create_visita({"Resumo": "Sem lead", "Lead": []})


def test_update_visita_passes_record_id_and_fields_through():
    fake_table = MagicMock()
    fake_table.update.return_value = {"id": "recVisita1", "fields": {"Lead": ["recLead2"]}}

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.update_visita(
            "recVisita1", {"Lead": ["recLead2"], "Imóvel": ["recImovel1"]}
        )

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.update.assert_called_once_with(
        "recVisita1", {"Lead": ["recLead2"], "Imóvel": ["recImovel1"]}
    )
    assert result == {"id": "recVisita1", "fields": {"Lead": ["recLead2"]}}


def test_delete_visita_calls_table_delete():
    fake_table = MagicMock()

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        visitas.delete_visita("recVisita1")

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.delete.assert_called_once_with("recVisita1")


def test_get_visita_wraps_table_get():
    fake_table = MagicMock()
    fake_table.get.return_value = {"id": "recVisita1", "fields": {}}

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.get_visita("recVisita1")

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.get.assert_called_once_with("recVisita1")
    assert result == {"id": "recVisita1", "fields": {}}


def test_list_visitas_by_date_range_builds_formula_and_returns_results():
    fake_table = MagicMock()
    fake_table.all.return_value = [{"id": "recVisita1", "fields": {}}]
    start = datetime(2026, 7, 15, 0, 0, 0)
    end = datetime(2026, 7, 16, 0, 0, 0)

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.list_visitas_by_date_range(start, end)

    mock_get_table.assert_called_once_with("Visitas")
    expected_formula = str(
        AND(
            IS_AFTER(Field("Data"), datetime_to_iso_str(start)),
            IS_BEFORE(Field("Data"), datetime_to_iso_str(end)),
        )
    )
    fake_table.all.assert_called_once_with(formula=expected_formula)
    assert result == [{"id": "recVisita1", "fields": {}}]


def test_list_visitas_by_lead_filters_by_membership_and_sorts_by_date():
    fake_table = MagicMock()
    fake_table.all.return_value = [
        {"id": "recLater", "fields": {"Lead": ["recLead1"], "Data": "2026-07-16T10:00:00.000Z"}},
        {
            "id": "recOtherLead",
            "fields": {"Lead": ["recLead2"], "Data": "2026-07-14T10:00:00.000Z"},
        },
        {
            "id": "recEarlier",
            "fields": {"Lead": ["recLead1"], "Data": "2026-07-14T10:00:00.000Z"},
        },
        {"id": "recNoLead", "fields": {"Data": "2026-07-15T10:00:00.000Z"}},
    ]

    with patch.object(visitas, "get_table", return_value=fake_table) as mock_get_table:
        result = visitas.list_visitas_by_lead("recLead1")

    mock_get_table.assert_called_once_with("Visitas")
    fake_table.all.assert_called_once_with()
    assert [r["id"] for r in result] == ["recEarlier", "recLater"]
