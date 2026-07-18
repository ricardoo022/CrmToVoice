import pytest
from pydantic import ValidationError

from crmToVoice.models.interpretation import Interpretation


def test_interpretation_minimal_construction_defaults_extracted_fields_empty():
    interpretation = Interpretation(intent="create", target_entity="Lead")

    assert interpretation.extracted_fields == {}


def test_interpretation_rejects_invalid_intent():
    with pytest.raises(ValidationError):
        Interpretation(
            intent="bogus",  # pyright: ignore[reportArgumentType]
            target_entity="Lead",
        )


def test_interpretation_accepts_extracted_fields_dict():
    interpretation = Interpretation(
        intent="update",
        target_entity="Property",
        extracted_fields={"Preço": 250000, "Estado": "Reservado"},
    )

    assert interpretation.extracted_fields == {"Preço": 250000, "Estado": "Reservado"}


def test_interpretation_defaults_intent_and_target_entity_to_none():
    interpretation = Interpretation()

    assert interpretation.intent is None
    assert interpretation.target_entity is None


def test_interpretation_allows_intent_without_a_resolved_target_entity():
    interpretation = Interpretation(intent="read")

    assert interpretation.intent == "read"
    assert interpretation.target_entity is None
