from langchain_core.tools import tool
from pyairtable.api.types import RecordDict

from crmToVoice.airtable import imoveis as _imoveis


@tool
def create_imovel(fields: dict) -> RecordDict:
    """Create an Imóvel (property) record in Airtable."""
    return _imoveis.create_imovel(fields)


@tool
def update_imovel(record_id: str, fields: dict) -> RecordDict:
    """Update an Imóvel (property) record in Airtable."""
    return _imoveis.update_imovel(record_id, fields)


@tool
def delete_imovel(record_id: str) -> None:
    """Delete an Imóvel (property) record from Airtable."""
    return _imoveis.delete_imovel(record_id)


@tool
def search_imoveis(morada: str) -> list[RecordDict]:
    """Search for Imóvel (property) records by Morada (address) in Airtable."""
    return _imoveis.search_imoveis(morada)


@tool
def get_imovel(record_id: str) -> dict:
    """Get an Imóvel (property) record by ID, including expanded Visitas."""
    return _imoveis.get_imovel(record_id)
