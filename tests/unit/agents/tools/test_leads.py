from unittest.mock import patch

from crmToVoice.agents.tools import leads
from crmToVoice.airtable import leads as airtable_leads


def test_create_lead_calls_airtable_with_same_fields():
    mock_result = {"id": "recNew", "fields": {"Nome": "Maria"}}

    with patch.object(airtable_leads, "create_lead", return_value=mock_result) as mock_fn:
        result = leads.create_lead.invoke({"fields": {"Nome": "Maria"}})

    mock_fn.assert_called_once_with({"Nome": "Maria"})
    assert result == mock_result


def test_update_lead_calls_airtable_with_record_id_and_fields():
    mock_result = {"id": "rec1", "fields": {"Estado": "Contactado"}}

    with patch.object(airtable_leads, "update_lead", return_value=mock_result) as mock_fn:
        result = leads.update_lead.invoke({"record_id": "rec1", "fields": {"Estado": "Contactado"}})

    mock_fn.assert_called_once_with("rec1", {"Estado": "Contactado"})
    assert result == mock_result


def test_delete_lead_calls_airtable_with_record_id():
    with patch.object(airtable_leads, "delete_lead", return_value=None) as mock_fn:
        result = leads.delete_lead.invoke({"record_id": "rec1"})

    mock_fn.assert_called_once_with("rec1")
    assert result is None


def test_search_leads_calls_airtable_with_nome():
    mock_result = [{"id": "rec1", "fields": {"Nome": "João Silva"}}]

    with patch.object(airtable_leads, "search_leads", return_value=mock_result) as mock_fn:
        result = leads.search_leads.invoke({"nome": "joão"})

    mock_fn.assert_called_once_with("joão")
    assert result == mock_result


def test_get_lead_calls_airtable_with_record_id():
    mock_result = {
        "id": "rec1",
        "fields": {"Nome": "João", "Visitas": ["recV1", "recV2"]},
        "visitas": [{"id": "recV1", "fields": {}}, {"id": "recV2", "fields": {}}],
    }

    with patch.object(airtable_leads, "get_lead", return_value=mock_result) as mock_fn:
        result = leads.get_lead.invoke({"record_id": "rec1"})

    mock_fn.assert_called_once_with("rec1")
    assert result == mock_result
