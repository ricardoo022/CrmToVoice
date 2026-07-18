"""Factory for the Tag 1 `interpret_speech` agent.

Builds the `create_agent` LangChain agent bound to all 18 CRM tools (Leads,
Imóveis, Visitas — read and write). This is the single all-tools agent
described in `docs/Agent.md` (Tag 1 section) and
`docs/backlog/epics/epic-03-tag-1-single-agent.md` (US-T1-01): no separate
read-only router, no StateGraph, no `interrupt()`, no wizard, no structured
`response_format` — the agent decides autonomously which tools to call and
replies with free-form Portuguese text.

`create_agent()` itself is not given a system prompt: the caller (webhook,
tests) builds a fresh `SystemMessage(content=render_system_prompt())` per
request instead, so the `{{TODAY}}`/`{{WEEKDAY}}` date anchor in the prompt
(see `prompt.py`) stays current on every call rather than being baked into
a cached agent at construction time.
"""

from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

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
from crmToVoice.config import get_chat_model


def create_interpret_speech_agent(checkpointer: BaseCheckpointSaver | bool | None = None):
    """Build the Tag 1 `interpret_speech` agent.

    Bound to all 18 CRM tools (read + write) — this agent can create, read,
    update, and delete Leads/Imóveis/Visitas directly. No `response_format`:
    the agent replies with free-form text for a Shortcut to speak aloud.
    """
    return create_agent(
        model=get_chat_model(),
        tools=[
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
        ],
        checkpointer=checkpointer,
    )
