import uuid

import pytest
import requests
from langchain_core.messages import ToolMessage

from crmToVoice.agents.catalog.interpret_speech import create_interpret_speech_agent
from crmToVoice.agents.catalog.interpret_speech.prompt import render_system_prompt
from crmToVoice.airtable import leads as airtable_leads
from crmToVoice.airtable.client import get_table


def _unique_name(base: str) -> str:
    """Adds a short suffix to avoid collisions with real data."""
    return f"{base} ({uuid.uuid4().hex[:6]})"


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


def _tool_messages(messages, tool_name: str | None = None) -> list[ToolMessage]:
    result = [m for m in messages if isinstance(m, ToolMessage)]
    if tool_name is not None:
        result = [m for m in result if m.name == tool_name]
    return result


def _system_message() -> dict:
    return {"role": "system", "content": render_system_prompt()}


def _invoke(agent, text: str, thread_id: str | None = None):
    return agent.invoke(
        {"messages": [_system_message(), {"role": "user", "content": text}]},
        config={"configurable": {"thread_id": thread_id or str(uuid.uuid4())}},
    )


def test_create_lead_dictation_creates_matching_lead_in_airtable(cleanup):
    # The disambiguation suffix (e.g. "(0eb01e)") is not a real part of a
    # person's name, so a well-behaved agent strips it before writing to
    # Airtable — search by the base name only, and disambiguate matches by
    # budget instead (unique enough for this test's purposes).
    base_name = "Sofia Almeida"
    name = _unique_name(base_name)

    agent = create_interpret_speech_agent()
    _invoke(
        agent,
        f"Novo lead. {name}, quer um apartamento de 2 quartos até 250 mil, "
        "contacto por referência da Ana.",
    )

    matches = [
        m for m in airtable_leads.search_leads(base_name) if m["fields"].get("Orçamento") == 250000
    ]
    assert matches, f"expected a Lead matching {base_name!r} to exist in Airtable"
    for match in matches:
        cleanup("Leads", match["id"])

    fields = matches[0]["fields"]
    assert base_name in str(fields.get("Nome"))
    assert fields.get("Orçamento") == 250000


def test_read_question_about_existing_lead_surfaces_lookup_and_status(cleanup):
    name = _unique_name("João Silva")
    created = airtable_leads.create_lead(
        {"Nome": name, "Estado": "Em Negociação", "Próximo Passo": "Enviar proposta"}
    )
    cleanup("Leads", created["id"])

    agent = create_interpret_speech_agent()
    result = _invoke(agent, f"Qual é o próximo passo com o {name}?")

    find_calls = _tool_messages(result["messages"], "find_lead") or _tool_messages(
        result["messages"], "search_leads"
    )
    assert find_calls, "expected a find_lead or search_leads tool call"

    reply = result["messages"][-1].content
    assert "proposta" in str(reply).lower()


def test_update_utterance_changes_lead_status_in_airtable(cleanup):
    name = _unique_name("Zé Pereira")
    created = airtable_leads.create_lead({"Nome": name, "Estado": "Em Negociação"})
    cleanup("Leads", created["id"])

    agent = create_interpret_speech_agent()
    _invoke(agent, f"O {name} já não está interessado.")

    refreshed = airtable_leads.get_lead(created["id"])
    assert refreshed["fields"].get("Estado") == "Perdido"


def test_delete_lead_requires_confirmation_before_deleting(cleanup):
    name = _unique_name("António Rodrigues")
    created = airtable_leads.create_lead({"Nome": name})
    cleanup("Leads", created["id"])

    agent = create_interpret_speech_agent()
    thread_id = str(uuid.uuid4())

    first = _invoke(agent, f"Apaga o lead do {name}.", thread_id=thread_id)
    delete_calls_before_confirmation = _tool_messages(first["messages"], "delete_lead")
    assert not delete_calls_before_confirmation, (
        "delete_lead must not be called before the person confirms"
    )

    messages_so_far = first["messages"] + [{"role": "user", "content": "Sim, confirmo."}]
    agent.invoke(
        {"messages": messages_so_far},
        config={"configurable": {"thread_id": thread_id}},
    )

    with pytest.raises(requests.exceptions.HTTPError):
        airtable_leads.get_lead(created["id"])


def test_no_lookup_for_brand_new_lead(cleanup):
    # Use a first name with an embedded random token (not a "(suffix)" the
    # agent might reasonably strip as noise) so this is unambiguously a
    # never-seen-before name, and register any created record for cleanup
    # so a passing run never leaks a "brand new lead" fixture for a future
    # run to collide with.
    name = f"Maria{uuid.uuid4().hex[:6].capitalize()} Costa"

    agent = create_interpret_speech_agent()
    result = _invoke(
        agent,
        f"Novo lead. {name}, quer um apartamento de 2 quartos até 250 mil, "
        "contacto por referência da Ana.",
    )

    assert _tool_messages(result["messages"], "find_lead") == []
    assert _tool_messages(result["messages"], "search_leads") == []

    for match in airtable_leads.search_leads(name):
        cleanup("Leads", match["id"])
