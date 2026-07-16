from langchain_core.tools import tool
from pyairtable.api.types import RecordDict

from crmToVoice.airtable import leads as _leads


@tool
def create_lead(fields: dict) -> RecordDict:
    """Create a Lead record in Airtable."""
    return _leads.create_lead(fields)


@tool
def update_lead(record_id: str, fields: dict) -> RecordDict:
    """Update a Lead record in Airtable."""
    return _leads.update_lead(record_id, fields)


@tool
def delete_lead(record_id: str) -> None:
    """Delete a Lead record from Airtable."""
    return _leads.delete_lead(record_id)


@tool
def search_leads(nome: str) -> list[RecordDict]:
    """Search for Lead records by name in Airtable."""
    return _leads.search_leads(nome)


@tool
def get_lead(record_id: str) -> dict:
    """Retrieve a Lead record from Airtable with expanded Visitas."""
    return _leads.get_lead(record_id)
