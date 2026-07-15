import pytest
from pydantic import ValidationError

from crmToVoice.models.fields import PropertyFields


def test_property_fields_all_fields_optional_can_construct_empty():
    imovel = PropertyFields()

    assert imovel.estado == "Disponível"
    assert imovel.morada is None
    assert imovel.tipo is None
    assert imovel.preco is None
    assert imovel.visitas is None


def test_property_fields_dump_by_alias_produces_airtable_keys():
    imovel = PropertyFields(morada="Rua das Flores 12", preco=250000)

    result = imovel.model_dump(by_alias=True, exclude_none=True)

    assert result == {
        "Morada": "Rua das Flores 12",
        "Preço": 250000,
        "Estado": "Disponível",
    }


def test_property_fields_rejects_invalid_tipo_choice():
    with pytest.raises(ValidationError):
        PropertyFields(tipo="Bogus")  # pyright: ignore[reportArgumentType]
