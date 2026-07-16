from datetime import datetime

from langchain_core.tools import tool
from pyairtable.api.types import RecordDict

from crmToVoice.airtable import visitas as _visitas


@tool
def create_visita(fields: dict) -> RecordDict:
    """Create a Visita (visit/interaction) record in Airtable, linked to a Lead."""
    return _visitas.create_visita(fields)


@tool
def update_visita(record_id: str, fields: dict) -> RecordDict:
    """Update a Visita record in Airtable with new field values."""
    return _visitas.update_visita(record_id, fields)


@tool
def delete_visita(record_id: str) -> None:
    """Delete a Visita record from Airtable."""
    return _visitas.delete_visita(record_id)


@tool
def get_visita(record_id: str) -> RecordDict:
    """Retrieve a single Visita record from Airtable by its record ID."""
    return _visitas.get_visita(record_id)


@tool
def list_visitas_by_date_range(start: datetime, end: datetime) -> list[RecordDict]:
    """List all Visita records within a date range."""
    return _visitas.list_visitas_by_date_range(start, end)


@tool
def list_visitas_by_lead(lead_record_id: str) -> list[RecordDict]:
    """List all Visita records linked to a specific Lead."""
    return _visitas.list_visitas_by_lead(lead_record_id)
