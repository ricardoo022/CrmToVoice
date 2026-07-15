import pytest
from pydantic import ValidationError

from crmToVoice.models.state import AgentState


def test_agent_state_minimal_construction_has_expected_defaults():
    state = AgentState(session_id="s1", current_input="hello")

    assert state.pending_question is None
    assert state.awaiting_delete_confirmation is False
    assert state.skipped_fields == []
    assert state.intent is None
    assert state.target_entity is None
    assert state.crm_context == {}
    assert state.extracted_fields == {}
    assert state.final_response is None


def test_agent_state_requires_session_id_and_current_input():
    with pytest.raises(ValidationError):
        AgentState()  # pyright: ignore[reportCallIssue]


def test_agent_state_accepts_full_set_of_fields():
    state = AgentState(
        session_id="s1",
        current_input="log a visit for João",
        intent="create",
        target_entity="Visit",
        crm_context={"lead_id": "rec1"},
        extracted_fields={"Nome": "João"},
        skipped_fields=["Telefone"],
        pending_question="What time was the visit?",
        awaiting_delete_confirmation=True,
        final_response="Visit logged.",
    )

    assert state.session_id == "s1"
    assert state.current_input == "log a visit for João"
    assert state.intent == "create"
    assert state.target_entity == "Visit"
    assert state.crm_context == {"lead_id": "rec1"}
    assert state.extracted_fields == {"Nome": "João"}
    assert state.skipped_fields == ["Telefone"]
    assert state.pending_question == "What time was the visit?"
    assert state.awaiting_delete_confirmation is True
    assert state.final_response == "Visit logged."


def test_agent_state_rejects_invalid_intent_value():
    with pytest.raises(ValidationError):
        AgentState(
            session_id="s1",
            current_input="hello",
            intent="bogus",  # pyright: ignore[reportArgumentType]
        )


def test_agent_state_rejects_invalid_target_entity_value():
    with pytest.raises(ValidationError):
        AgentState(
            session_id="s1",
            current_input="hello",
            target_entity="bogus",  # pyright: ignore[reportArgumentType]
        )
