import uuid
from datetime import datetime, timedelta, timezone

import pytest
from requests.exceptions import HTTPError

from crmToVoice.airtable import visitas
from crmToVoice.airtable.client import get_table
from crmToVoice.models import VisitFields


def _unique_name(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4().hex[:8]}"


@pytest.fixture
def lead_id():
    record = get_table("Leads").create({"Nome": _unique_name("US-DB-04 Lead")})
    yield record["id"]
    get_table("Leads").delete(record["id"])


@pytest.fixture
def visita_id(lead_id):
    created_ids = []

    def _make(fields=None):
        base_fields = {
            "Resumo": "Visita de teste",
            "Lead": [lead_id],
            "Data": datetime.now(timezone.utc).isoformat(),
        }
        record = visitas.create_visita({**base_fields, **(fields or {})})
        created_ids.append(record["id"])
        return record

    yield _make

    for record_id in created_ids:
        try:
            visitas.delete_visita(record_id)
        except Exception:
            pass


def test_create_visita_raises_without_real_airtable_call_when_lead_missing():
    with pytest.raises(ValueError, match="Lead"):
        visitas.create_visita({"Resumo": "Sem lead"})


def test_create_and_get_visita_roundtrip(lead_id, visita_id):
    created = visita_id()

    fetched = visitas.get_visita(created["id"])

    assert fetched["id"] == created["id"]
    assert fetched["fields"]["Resumo"] == "Visita de teste"
    assert fetched["fields"]["Lead"] == [lead_id]


def test_update_visita_reassigns_fields(lead_id, visita_id):
    created = visita_id()

    updated = visitas.update_visita(created["id"], {"Resumo": "Resumo atualizado"})

    assert updated["fields"]["Resumo"] == "Resumo atualizado"
    fetched = visitas.get_visita(created["id"])
    assert fetched["fields"]["Resumo"] == "Resumo atualizado"


def test_update_visita_reassigns_lead_link(lead_id, visita_id):
    created = visita_id()
    other_lead = get_table("Leads").create({"Nome": _unique_name("US-DB-04 Segundo Lead")})
    try:
        updated = visitas.update_visita(created["id"], {"Lead": [other_lead["id"]]})

        assert updated["fields"]["Lead"] == [other_lead["id"]]
        fetched = visitas.get_visita(created["id"])
        assert fetched["fields"]["Lead"] == [other_lead["id"]]
    finally:
        get_table("Leads").delete(other_lead["id"])


def test_delete_visita_removes_record(lead_id):
    created = visitas.create_visita({"Resumo": "Para apagar", "Lead": [lead_id]})

    visitas.delete_visita(created["id"])

    # A deleted record ID comes back as 403 (not 404) from the Airtable API,
    # and pyairtable re-raises that as a plain requests.HTTPError.
    with pytest.raises(HTTPError):
        get_table("Visitas").get(created["id"])


def test_list_visitas_by_date_range_finds_visita_created_now(lead_id, visita_id):
    created = visita_id()

    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    results = visitas.list_visitas_by_date_range(start, end)

    assert any(r["id"] == created["id"] for r in results)


def test_list_visitas_by_lead_returns_only_matching_lead(lead_id, visita_id):
    created = visita_id()

    other_lead = get_table("Leads").create({"Nome": _unique_name("US-DB-04 Outro Lead")})
    try:
        other_visita = visitas.create_visita({"Resumo": "Outra visita", "Lead": [other_lead["id"]]})
        try:
            results = visitas.list_visitas_by_lead(lead_id)

            ids = [r["id"] for r in results]
            assert created["id"] in ids
            assert other_visita["id"] not in ids
        finally:
            visitas.delete_visita(other_visita["id"])
    finally:
        get_table("Leads").delete(other_lead["id"])


def test_create_visita_accepts_visit_fields_dump_by_alias(lead_id):
    payload = VisitFields(
        resumo="US-AG-01 Contract",
        lead=[lead_id],
    ).model_dump(by_alias=True, exclude_none=True)

    created = visitas.create_visita(payload)

    try:
        assert created["fields"]["Resumo"] == "US-AG-01 Contract"
        assert created["fields"]["Lead"] == [lead_id]
        assert created["fields"]["Tipo"] == "Visita"
    finally:
        visitas.delete_visita(created["id"])


def test_list_visitas_by_lead_orders_results_by_date(lead_id, visita_id):
    later = visita_id({"Data": "2026-08-01T10:00:00.000Z"})
    earlier = visita_id({"Data": "2026-07-01T10:00:00.000Z"})

    results = visitas.list_visitas_by_lead(lead_id)
    ids = [r["id"] for r in results]

    assert ids.index(earlier["id"]) < ids.index(later["id"])
