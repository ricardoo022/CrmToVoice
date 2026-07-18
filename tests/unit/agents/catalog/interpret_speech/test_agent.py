from unittest.mock import MagicMock, patch

from crmToVoice.agents.catalog.interpret_speech import agent as agent_module
from crmToVoice.agents.catalog.interpret_speech.agent import create_interpret_speech_agent
from crmToVoice.agents.tools import (
    create_imovel,
    create_lead,
    create_visita,
    delete_imovel,
    delete_lead,
    delete_visita,
    find_imovel,
    find_lead,
    get_imovel,
    get_lead,
    get_visita,
    list_visitas_by_date_range,
    list_visitas_by_lead,
    search_imoveis,
    search_leads,
    update_imovel,
    update_lead,
    update_visita,
)


def test_create_interpret_speech_agent_binds_all_eighteen_tools():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent()

    _, kwargs = mock_create_agent.call_args
    assert kwargs["tools"] == [
        create_lead,
        update_lead,
        delete_lead,
        search_leads,
        get_lead,
        find_lead,
        create_imovel,
        update_imovel,
        delete_imovel,
        search_imoveis,
        get_imovel,
        find_imovel,
        create_visita,
        update_visita,
        delete_visita,
        get_visita,
        list_visitas_by_date_range,
        list_visitas_by_lead,
    ]


def test_create_interpret_speech_agent_uses_configured_chat_model():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent()

    _, kwargs = mock_create_agent.call_args
    assert kwargs["model"] is mock_model


def test_create_interpret_speech_agent_does_not_pass_system_prompt():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent()

    _, kwargs = mock_create_agent.call_args
    assert "system_prompt" not in kwargs


def test_create_interpret_speech_agent_does_not_pass_response_format():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent()

    _, kwargs = mock_create_agent.call_args
    assert "response_format" not in kwargs


def test_create_interpret_speech_agent_defaults_checkpointer_to_none():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent()

    _, kwargs = mock_create_agent.call_args
    assert kwargs["checkpointer"] is None


def test_create_interpret_speech_agent_forwards_explicit_checkpointer():
    mock_model = MagicMock(name="chat_model")
    sentinel_checkpointer = MagicMock(name="checkpointer")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        create_interpret_speech_agent(checkpointer=sentinel_checkpointer)

    _, kwargs = mock_create_agent.call_args
    assert kwargs["checkpointer"] is sentinel_checkpointer


def test_create_interpret_speech_agent_returns_create_agent_result():
    mock_model = MagicMock(name="chat_model")

    with (
        patch.object(agent_module, "get_chat_model", return_value=mock_model),
        patch.object(agent_module, "create_agent") as mock_create_agent,
    ):
        result = create_interpret_speech_agent()

    assert result is mock_create_agent.return_value
