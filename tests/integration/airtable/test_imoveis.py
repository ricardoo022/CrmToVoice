import uuid

import pytest
import requests

from crmToVoice.airtable import imoveis
from crmToVoice.airtable.client import get_table


def _unique_morada(prefix: str) -> str:
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


def test_create_and_get_imovel_roundtrip(cleanup):
    morada = _unique_morada("US-DB-03 Create")
    created = imoveis.create_imovel({"Morada": morada})
    cleanup("Imóveis", created["id"])

    fetched = imoveis.get_imovel(created["id"])

    assert fetched["fields"]["Morada"] == morada
    assert fetched["visitas"] == []


def test_update_imovel_changes_estado(cleanup):
    created = imoveis.create_imovel({"Morada": _unique_morada("US-DB-03 Update")})
    cleanup("Imóveis", created["id"])

    updated = imoveis.update_imovel(created["id"], {"Estado": "Reservado"})

    assert updated["fields"]["Estado"] == "Reservado"


def test_delete_imovel_removes_record():
    created = imoveis.create_imovel({"Morada": _unique_morada("US-DB-03 Delete")})

    imoveis.delete_imovel(created["id"])

    with pytest.raises(requests.exceptions.HTTPError):
        get_table("Imóveis").get(created["id"])


def test_search_imoveis_finds_partial_case_insensitive_match(cleanup):
    unique_token = uuid.uuid4().hex[:8]
    morada = f"Rua das Flores {unique_token} Lisboa"
    created = imoveis.create_imovel({"Morada": morada})
    cleanup("Imóveis", created["id"])

    results = imoveis.search_imoveis(f"flores {unique_token}".upper())

    assert any(r["id"] == created["id"] for r in results)


def test_get_imovel_expands_linked_visita(cleanup):
    imovel = imoveis.create_imovel({"Morada": _unique_morada("US-DB-03 Visita")})
    cleanup("Imóveis", imovel["id"])

    lead = get_table("Leads").create({"Nome": _unique_morada("US-DB-03 Lead")})
    cleanup("Leads", lead["id"])

    visita = get_table("Visitas").create(
        {
            "Título": _unique_morada("US-DB-03 Visita Título"),
            "Lead": [lead["id"]],
            "Imóvel": [imovel["id"]],
        }
    )
    cleanup("Visitas", visita["id"])

    fetched = imoveis.get_imovel(imovel["id"])

    assert len(fetched["visitas"]) == 1
    assert fetched["visitas"][0]["id"] == visita["id"]
