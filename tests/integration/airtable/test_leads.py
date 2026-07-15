import uuid

import pytest
import requests

from crmToVoice.airtable import leads
from crmToVoice.airtable.client import get_table
from crmToVoice.models import LeadFields


def _unique_name(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4().hex[:8]}"


@pytest.fixture
def cleanup():
    created: list[tuple[str, str]] = []

    def register(table_name: str, record_id: str) -> str:
        created.append((table_name, record_id))
        return record_id

    yield register

    for table_name, record_id in created:
        try:
            get_table(table_name).delete(record_id)
        except requests.exceptions.HTTPError:
            pass


def test_create_and_get_lead_roundtrip(cleanup):
    name = _unique_name("US-DB-02 Create")
    created = leads.create_lead({"Nome": name})
    cleanup("Leads", created["id"])

    fetched = leads.get_lead(created["id"])

    assert fetched["fields"]["Nome"] == name
    assert fetched["visitas"] == []


def test_update_lead_changes_field(cleanup):
    created = leads.create_lead({"Nome": _unique_name("US-DB-02 Update")})
    cleanup("Leads", created["id"])

    updated = leads.update_lead(created["id"], {"Próximo Passo": "Ligar amanhã"})

    assert updated["fields"]["Próximo Passo"] == "Ligar amanhã"


def test_delete_lead_removes_record():
    created = leads.create_lead({"Nome": _unique_name("US-DB-02 Delete")})

    leads.delete_lead(created["id"])

    with pytest.raises(requests.exceptions.HTTPError):
        get_table("Leads").get(created["id"])


def test_search_leads_finds_partial_case_insensitive_match(cleanup):
    unique_token = uuid.uuid4().hex[:8]
    name = f"Joãozinho {unique_token} Ferreira"
    created = leads.create_lead({"Nome": name})
    cleanup("Leads", created["id"])

    results = leads.search_leads(f"joãozinho {unique_token}".upper())

    assert any(r["id"] == created["id"] for r in results)


def test_get_lead_expands_linked_visita(cleanup):
    lead = leads.create_lead({"Nome": _unique_name("US-DB-02 Visita")})
    cleanup("Leads", lead["id"])

    visita = get_table("Visitas").create(
        {"Título": _unique_name("US-DB-02 Visita Título"), "Lead": [lead["id"]]}
    )
    cleanup("Visitas", visita["id"])

    fetched = leads.get_lead(lead["id"])

    assert len(fetched["visitas"]) == 1
    assert fetched["visitas"][0]["id"] == visita["id"]


def test_create_lead_accepts_lead_fields_dump_by_alias(cleanup):
    payload = LeadFields(
        nome=_unique_name("US-AG-01 Contract"),
        telefone="912345678",
        orcamento=250000,
    ).model_dump(by_alias=True, exclude_none=True)

    created = leads.create_lead(payload)
    cleanup("Leads", created["id"])

    assert created["fields"]["Nome"] == payload["Nome"]
    assert created["fields"]["Orçamento"] == 250000
