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


@tool
def find_lead(nome: str) -> dict:
    """Find a Lead by name and return the full record with visit history.

    Use this when you need to find an existing Lead by name and see their
    details including all linked visits. Combines search + get in one call.

    Args:
        nome: The Lead's name to search for (partial match, case-insensitive)

    Returns:
        A dict with "found" (bool) and, if found, the full Lead record
        including "visitas" (list of expanded Visit records).
    """
    leads = _leads.search_leads(nome)
    if not leads:
        return {"found": False, "lead": None, "visitas": []}
    full_lead = _leads.get_lead(leads[0]["id"])
    return {"found": True, **full_lead}
