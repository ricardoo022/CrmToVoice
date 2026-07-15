from pyairtable.api.types import RecordDict
from pyairtable.formulas import LOWER, SEARCH, Field

from crmToVoice.airtable.client import get_records_by_ids, get_table

TABLE_NAME = "Imóveis"


def create_imovel(fields: dict) -> RecordDict:
    return get_table(TABLE_NAME).create(fields)


def update_imovel(record_id: str, fields: dict) -> RecordDict:
    return get_table(TABLE_NAME).update(record_id, fields)


def delete_imovel(record_id: str) -> None:
    get_table(TABLE_NAME).delete(record_id)


def search_imoveis(morada: str) -> list[RecordDict]:
    formula = SEARCH(morada.lower(), LOWER(Field("Morada")))
    return get_table(TABLE_NAME).all(formula=str(formula))


def get_imovel(record_id: str) -> dict:
    imovel = get_table(TABLE_NAME).get(record_id)
    visita_ids = imovel["fields"].get("Visitas", [])
    return {**imovel, "visitas": get_records_by_ids("Visitas", visita_ids)}
