from langchain_core.tools import tool
from pyairtable.api.types import RecordDict

from crmToVoice.airtable import leads as airtable_leads


@tool
def create_lead(fields: dict) -> RecordDict:
    """Create a Lead record in Airtable."""
    return airtable_leads.create_lead(fields)


@tool
def update_lead(record_id: str, fields: dict) -> RecordDict:
    """Update a Lead record in Airtable."""
    return airtable_leads.update_lead(record_id, fields)


@tool
def delete_lead(record_id: str) -> None:
    """Delete a Lead record from Airtable."""
    return airtable_leads.delete_lead(record_id)


@tool
def search_leads(nome: str) -> list[RecordDict]:
    """Search for Lead records by name in Airtable."""
    return airtable_leads.search_leads(nome)


@tool
def get_lead(record_id: str) -> dict:
    """Retrieve a Lead record from Airtable with expanded Visitas."""
    return airtable_leads.get_lead(record_id)
