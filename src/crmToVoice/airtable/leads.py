from pyairtable.api.types import RecordDict
from pyairtable.formulas import LOWER, SEARCH, Field

from crmToVoice.airtable.client import get_records_by_ids, get_table

TABLE_NAME = "Leads"


def create_lead(fields: dict) -> RecordDict:
    return get_table(TABLE_NAME).create(fields)


def update_lead(record_id: str, fields: dict) -> RecordDict:
    return get_table(TABLE_NAME).update(record_id, fields)


def delete_lead(record_id: str) -> None:
    get_table(TABLE_NAME).delete(record_id)


def search_leads(nome: str) -> list[RecordDict]:
    formula = SEARCH(nome.lower(), LOWER(Field("Nome")))
    return get_table(TABLE_NAME).all(formula=str(formula))


def get_lead(record_id: str) -> dict:
    lead = get_table(TABLE_NAME).get(record_id)
    visita_ids = lead["fields"].get("Visitas", [])
    return {**lead, "visitas": get_records_by_ids("Visitas", visita_ids)}
