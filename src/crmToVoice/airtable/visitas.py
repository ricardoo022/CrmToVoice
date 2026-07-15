from datetime import datetime

from pyairtable.api.types import RecordDict
from pyairtable.formulas import AND, IS_AFTER, IS_BEFORE, Field
from pyairtable.utils import datetime_to_iso_str

from crmToVoice.airtable.client import get_table


def create_visita(fields: dict) -> RecordDict:
    if not fields.get("Lead"):
        raise ValueError("create_visita requires a non-empty 'Lead' link")
    return get_table("Visitas").create(fields)


def update_visita(record_id: str, fields: dict) -> RecordDict:
    return get_table("Visitas").update(record_id, fields)


def delete_visita(record_id: str) -> None:
    get_table("Visitas").delete(record_id)


def get_visita(record_id: str) -> RecordDict:
    return get_table("Visitas").get(record_id)


def list_visitas_by_date_range(start: datetime, end: datetime) -> list[RecordDict]:
    # Bounds are exclusive (IS_AFTER/IS_BEFORE); widen by a second on either
    # side if inclusive bounds are ever needed.
    formula = AND(
        IS_AFTER(Field("Data"), datetime_to_iso_str(start)),
        IS_BEFORE(Field("Data"), datetime_to_iso_str(end)),
    )
    return get_table("Visitas").all(formula=str(formula))


def list_visitas_by_lead(lead_record_id: str) -> list[RecordDict]:
    # Linked-record formulas match on the linked record's primary-field text,
    # not its record ID, so exact-ID filtering has to happen client-side.
    records = get_table("Visitas").all()
    matching = [r for r in records if lead_record_id in r["fields"].get("Lead", [])]
    # Airtable omits a field from the response entirely when it has no value,
    # so a Visita with no Data yet (e.g. create_visita called without it —
    # Data isn't auto-filled at this layer, that's Epic 02's job) must not
    # crash the sort; treat it as sorting first, ahead of any known date.
    return sorted(matching, key=lambda r: r["fields"].get("Data", ""))
