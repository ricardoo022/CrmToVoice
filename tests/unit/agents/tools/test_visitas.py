from datetime import datetime
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from crmToVoice.agents.tools import visitas
from crmToVoice.airtable import visitas as airtable_visitas


def test_create_visita_passes_through_to_airtable():
    """Test that create_visita tool calls the airtable function and returns the result."""
    fake_record = {"id": "recVisita1", "fields": {"Lead": ["recLead1"], "Resumo": "Correu bem"}}

    with patch.object(airtable_visitas, "create_visita", return_value=fake_record) as mock_create:
        result = visitas.create_visita.invoke(
            {"fields": {"Resumo": "Correu bem", "Lead": ["recLead1"]}}
        )

    mock_create.assert_called_once_with({"Resumo": "Correu bem", "Lead": ["recLead1"]})
    assert result == fake_record


def test_create_visita_propagates_value_error_when_lead_missing():
    """Test that create_visita tool propagates ValueError from airtable when Lead is missing."""
    with pytest.raises(ValueError, match="Lead"):
        visitas.create_visita.invoke({"fields": {"Resumo": "sem lead"}})


def test_create_visita_never_reaches_airtable_when_lead_missing():
    """The Lead-missing ValueError must be raised before any Airtable table access happens."""
    with patch.object(airtable_visitas, "get_table") as mock_get_table:
        with pytest.raises(ValueError, match="Lead"):
            visitas.create_visita.invoke({"fields": {"Resumo": "sem lead"}})

    mock_get_table.assert_not_called()


def test_update_visita_passes_through_to_airtable():
    """Test that update_visita tool calls the airtable function and returns the result."""
    fake_record = {"id": "recVisita1", "fields": {"Lead": ["recLead2"]}}

    with patch.object(airtable_visitas, "update_visita", return_value=fake_record) as mock_update:
        result = visitas.update_visita.invoke(
            {"record_id": "recVisita1", "fields": {"Lead": ["recLead2"]}}
        )

    mock_update.assert_called_once_with("recVisita1", {"Lead": ["recLead2"]})
    assert result == fake_record


def test_delete_visita_passes_through_to_airtable():
    """Test that delete_visita tool calls the airtable function."""
    with patch.object(airtable_visitas, "delete_visita", return_value=None) as mock_delete:
        result = visitas.delete_visita.invoke({"record_id": "recVisita1"})

    mock_delete.assert_called_once_with("recVisita1")
    assert result is None


def test_get_visita_passes_through_to_airtable():
    """Test that get_visita tool calls the airtable function and returns the result."""
    fake_record = {"id": "recVisita1", "fields": {"Lead": ["recLead1"]}}

    with patch.object(airtable_visitas, "get_visita", return_value=fake_record) as mock_get:
        result = visitas.get_visita.invoke({"record_id": "recVisita1"})

    mock_get.assert_called_once_with("recVisita1")
    assert result == fake_record


def test_list_visitas_by_date_range_passes_through_to_airtable():
    """Test list_visitas_by_date_range tool calls airtable and returns result."""
    start = datetime(2026, 7, 15, 0, 0, 0)
    end = datetime(2026, 7, 16, 0, 0, 0)
    fake_records = [{"id": "recVisita1", "fields": {}}]

    with patch.object(
        airtable_visitas, "list_visitas_by_date_range", return_value=fake_records
    ) as mock_list:
        result = visitas.list_visitas_by_date_range.invoke({"start": start, "end": end})

    mock_list.assert_called_once_with(start, end)
    assert result == fake_records


def test_list_visitas_by_lead_passes_through_to_airtable():
    """Test that list_visitas_by_lead tool calls the airtable function and returns the result."""
    fake_records = [
        {"id": "recVisita1", "fields": {"Lead": ["recLead1"], "Data": "2026-07-14T10:00:00.000Z"}},
        {"id": "recVisita2", "fields": {"Lead": ["recLead1"], "Data": "2026-07-16T10:00:00.000Z"}},
    ]

    with patch.object(
        airtable_visitas, "list_visitas_by_lead", return_value=fake_records
    ) as mock_list:
        result = visitas.list_visitas_by_lead.invoke({"lead_record_id": "recLead1"})

    mock_list.assert_called_once_with("recLead1")
    assert result == fake_records


def test_list_visitas_by_date_range_coerces_iso_strings_to_datetime():
    """LLM tool calls arrive as JSON, so start/end are ISO strings, not datetime objects;
    the inferred arg schema must coerce them before calling the airtable layer, which
    requires real datetime objects (it calls datetime_to_iso_str on them)."""
    fake_records = [{"id": "recVisita1", "fields": {}}]

    with patch.object(
        airtable_visitas, "list_visitas_by_date_range", return_value=fake_records
    ) as mock_list:
        result = visitas.list_visitas_by_date_range.invoke(
            {"start": "2026-07-15T00:00:00", "end": "2026-07-16T00:00:00"}
        )

    mock_list.assert_called_once_with(
        datetime(2026, 7, 15, 0, 0, 0), datetime(2026, 7, 16, 0, 0, 0)
    )
    called_start, called_end = mock_list.call_args[0]
    assert isinstance(called_start, datetime)
    assert isinstance(called_end, datetime)
    assert result == fake_records


def test_create_visita_rejects_non_dict_fields():
    """The inferred arg schema should actually validate `fields` as a dict, not accept anything."""
    with patch.object(airtable_visitas, "create_visita") as mock_fn:
        with pytest.raises(ValidationError):
            visitas.create_visita.invoke({"fields": ["not", "a", "dict"]})

    mock_fn.assert_not_called()
