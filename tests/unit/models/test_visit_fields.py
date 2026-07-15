import pytest
from pydantic import ValidationError

from crmToVoice.models.fields import VisitFields


def test_visit_fields_all_fields_optional_can_construct_empty():
    visita = VisitFields()

    assert visita.tipo == "Visita"
    assert visita.lead is None
    assert visita.titulo is None
    assert visita.data is None
    assert visita.resumo is None
    assert visita.sentimento is None
    assert visita.proximos_passos is None
    assert visita.imovel is None


def test_visit_fields_dump_by_alias_produces_airtable_keys():
    visita = VisitFields(resumo="Cliente gostou da cozinha.", lead=["recABC"])

    result = visita.model_dump(by_alias=True, exclude_none=True)

    assert result == {
        "Resumo": "Cliente gostou da cozinha.",
        "Tipo": "Visita",
        "Lead": ["recABC"],
    }


def test_visit_fields_rejects_invalid_sentimento_choice():
    with pytest.raises(ValidationError):
        VisitFields(sentimento="Bogus")  # pyright: ignore[reportArgumentType]
