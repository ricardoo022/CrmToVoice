import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from crmToVoice import webhook


@pytest.fixture(autouse=True)
def _reset_agent_cache():
    webhook._get_agent.cache_clear()
    webhook._session_history.clear()
    webhook._session_locks.clear()
    yield
    webhook._get_agent.cache_clear()
    webhook._session_history.clear()
    webhook._session_locks.clear()


@pytest.fixture
def client():
    return TestClient(webhook.app)


def test_valid_request_returns_reply_from_last_ai_message(client):
    mock_agent = type(
        "MockAgent",
        (),
        {
            "invoke": lambda self, payload: {
                "messages": [
                    HumanMessage(content="Que visitas tenho hoje?"),
                    AIMessage(content="Tens uma visita às 15h."),
                ]
            }
        },
    )()

    with patch.object(webhook, "_get_agent", return_value=mock_agent):
        response = client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Que visitas tenho hoje?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "session_id": "abc-123",
        "reply_text": "Tens uma visita às 15h.",
        "done": True,
    }


def test_reply_taken_from_last_ai_message_even_with_trailing_tool_messages(client):
    mock_agent = type(
        "MockAgent",
        (),
        {
            "invoke": lambda self, payload: {
                "messages": [
                    HumanMessage(content="Que visitas tenho hoje?"),
                    AIMessage(content="Vou verificar."),
                    ToolMessage(
                        content="[]", tool_call_id="call_1", name="list_visitas_by_date_range"
                    ),
                ]
            }
        },
    )()

    with patch.object(webhook, "_get_agent", return_value=mock_agent):
        response = client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Que visitas tenho hoje?"},
        )

    assert response.status_code == 200
    assert response.json()["reply_text"] == "Vou verificar."


def test_agent_exception_returns_http_500(client):
    mock_agent = type(
        "MockAgent",
        (),
        {"invoke": lambda self, payload: (_ for _ in ()).throw(RuntimeError("LLM timeout"))},
    )()

    with patch.object(webhook, "_get_agent", return_value=mock_agent):
        response = client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Qualquer coisa"},
        )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_invoke_called_with_system_message_then_human_message(client):
    captured_payloads = []

    class MockAgent:
        def invoke(self, payload):
            captured_payloads.append(payload)
            return {"messages": [AIMessage(content="ok")]}

    with patch.object(webhook, "_get_agent", return_value=MockAgent()):
        client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Novo lead, Maria Costa."},
        )

    assert len(captured_payloads) == 1
    messages = captured_payloads[0]["messages"]
    assert len(messages) == 2

    system_message, human_message = messages
    assert isinstance(system_message, SystemMessage)
    assert system_message.content
    assert isinstance(human_message, HumanMessage)
    assert human_message.content == "Novo lead, Maria Costa."


def test_no_ai_message_in_result_returns_http_500(client):
    mock_agent = type(
        "MockAgent",
        (),
        {"invoke": lambda self, payload: {"messages": [HumanMessage(content="oi")]}},
    )()

    with patch.object(webhook, "_get_agent", return_value=mock_agent):
        response = client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Qualquer coisa"},
        )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_blank_ai_message_content_returns_http_500(client):
    """A trailing AIMessage with empty content (e.g. only tool_calls, no
    text) is just as unusable as no AIMessage at all — must not silently
    return 200 with reply_text: "".
    """
    mock_agent = type(
        "MockAgent",
        (),
        {"invoke": lambda self, payload: {"messages": [AIMessage(content="")]}},
    )()

    with patch.object(webhook, "_get_agent", return_value=mock_agent):
        response = client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Qualquer coisa"},
        )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_concurrent_requests_to_same_session_are_serialized(client):
    """Two overlapping requests for the same session_id must not race on
    _session_history — the second must see the first's turn, not clobber it.
    """
    call_order: list[str] = []
    invocation_count = [0]
    barrier = threading.Barrier(2)

    class MockAgent:
        def invoke(self, payload):
            call_index = invocation_count[0]
            invocation_count[0] += 1
            call_order.append(f"start-{call_index}")
            if call_index == 0:
                # First call: wait for the second request to actually be
                # in flight before finishing, so without a lock they'd
                # interleave.
                barrier.wait(timeout=2)
                time.sleep(0.05)
            reply = f"reply-{call_index}"
            call_order.append(f"end-{call_index}")
            return {"messages": [*payload["messages"], AIMessage(content=reply)]}

    def post(text):
        return client.post("/webhook", json={"session_id": "shared", "text": text})

    with patch.object(webhook, "_get_agent", return_value=MockAgent()):
        results = []

        def first():
            results.append(post("primeiro"))

        def second():
            barrier.wait(timeout=2)
            results.append(post("segundo"))

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

    assert [r.status_code for r in results] == [200, 200]
    # The lock forces call 0 to fully finish (start-0, end-0) before call 1
    # starts — no interleaving.
    assert call_order == ["start-0", "end-0", "start-1", "end-1"]


def test_second_request_in_same_session_replays_prior_history(client):
    captured_payloads = []

    class MockAgent:
        def invoke(self, payload):
            captured_payloads.append(payload)
            reply = "Qual é o orçamento?" if len(captured_payloads) == 1 else "Ok, guardado."
            return {"messages": [*payload["messages"], AIMessage(content=reply)]}

    with patch.object(webhook, "_get_agent", return_value=MockAgent()):
        client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "Novo lead, Maria Costa."},
        )
        client.post(
            "/webhook",
            json={"session_id": "abc-123", "text": "250 mil."},
        )

    assert len(captured_payloads) == 2

    second_call_messages = captured_payloads[1]["messages"]
    contents = [m.content for m in second_call_messages]
    assert "Novo lead, Maria Costa." in contents
    assert "Qual é o orçamento?" in contents
    assert contents[-1] == "250 mil."


def test_different_sessions_do_not_share_history(client):
    captured_payloads = []

    class MockAgent:
        def invoke(self, payload):
            captured_payloads.append(payload)
            return {"messages": [*payload["messages"], AIMessage(content="ok")]}

    with patch.object(webhook, "_get_agent", return_value=MockAgent()):
        client.post("/webhook", json={"session_id": "session-a", "text": "Primeiro."})
        client.post("/webhook", json={"session_id": "session-b", "text": "Segundo."})

    second_call_messages = captured_payloads[1]["messages"]
    contents = [m.content for m in second_call_messages]
    assert "Primeiro." not in contents
