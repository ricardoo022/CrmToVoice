from unittest.mock import patch

from crmToVoice.agents.tools import leads


def test_create_lead_calls_airtable_with_same_fields():
    mock_result = {"id": "recNew", "fields": {"Nome": "Maria"}}

    with patch.object(leads, "airtable_leads") as mock_airtable_leads:  # Import alias pattern
        mock_airtable_leads.create_lead.return_value = mock_result
        # Import and use the function from the agents.tools module
        from crmToVoice.agents.tools.leads import create_lead

        result = create_lead.invoke({"fields": {"Nome": "Maria"}})

    mock_airtable_leads.create_lead.assert_called_once_with({"Nome": "Maria"})
    assert result == mock_result


def test_update_lead_calls_airtable_with_record_id_and_fields():
    mock_result = {"id": "rec1", "fields": {"Estado": "Contactado"}}

    with patch.object(leads, "airtable_leads") as mock_airtable_leads:
        mock_airtable_leads.update_lead.return_value = mock_result
        from crmToVoice.agents.tools.leads import update_lead

        result = update_lead.invoke({"record_id": "rec1", "fields": {"Estado": "Contactado"}})

    mock_airtable_leads.update_lead.assert_called_once_with("rec1", {"Estado": "Contactado"})
    assert result == mock_result


def test_delete_lead_calls_airtable_with_record_id():
    with patch.object(leads, "airtable_leads") as mock_airtable_leads:
        mock_airtable_leads.delete_lead.return_value = None
        from crmToVoice.agents.tools.leads import delete_lead

        result = delete_lead.invoke({"record_id": "rec1"})

    mock_airtable_leads.delete_lead.assert_called_once_with("rec1")
    assert result is None


def test_search_leads_calls_airtable_with_nome():
    mock_result = [{"id": "rec1", "fields": {"Nome": "João Silva"}}]

    with patch.object(leads, "airtable_leads") as mock_airtable_leads:
        mock_airtable_leads.search_leads.return_value = mock_result
        from crmToVoice.agents.tools.leads import search_leads

        result = search_leads.invoke({"nome": "joão"})

    mock_airtable_leads.search_leads.assert_called_once_with("joão")
    assert result == mock_result


def test_get_lead_calls_airtable_with_record_id():
    mock_result = {
        "id": "rec1",
        "fields": {"Nome": "João", "Visitas": ["recV1", "recV2"]},
        "visitas": [{"id": "recV1", "fields": {}}, {"id": "recV2", "fields": {}}],
    }

    with patch.object(leads, "airtable_leads") as mock_airtable_leads:
        mock_airtable_leads.get_lead.return_value = mock_result
        from crmToVoice.agents.tools.leads import get_lead

        result = get_lead.invoke({"record_id": "rec1"})

    mock_airtable_leads.get_lead.assert_called_once_with("rec1")
    assert result == mock_result
