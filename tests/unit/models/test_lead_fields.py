import pytest
from pydantic import ValidationError

from crmToVoice.models.fields import LeadFields


def test_lead_fields_all_fields_optional_can_construct_empty():
    lead = LeadFields()

    assert lead.estado == "Novo"
    assert lead.nome is None
    assert lead.telefone is None
    assert lead.email is None
    assert lead.tipo_de_imovel_procurado is None
    assert lead.orcamento is None
    assert lead.origem is None
    assert lead.sentimento is None
    assert lead.proximo_passo is None
    assert lead.data_ultima_interacao is None
    assert lead.visitas is None


def test_lead_fields_dump_by_alias_produces_airtable_keys():
    lead = LeadFields(nome="Maria", orcamento=250000)

    result = lead.model_dump(by_alias=True, exclude_none=True)

    assert result == {"Nome": "Maria", "Estado": "Novo", "Orçamento": 250000}


def test_lead_fields_accepts_construction_via_airtable_alias_keys():
    lead = LeadFields(**{"Nome": "Maria", "Orçamento": 250000})

    assert lead.nome == "Maria"
    assert lead.orcamento == 250000


def test_lead_fields_rejects_invalid_estado_choice():
    with pytest.raises(ValidationError):
        LeadFields(estado="Bogus")  # pyright: ignore[reportArgumentType]
