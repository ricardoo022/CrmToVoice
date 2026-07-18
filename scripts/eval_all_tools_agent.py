"""LangSmith evaluator suite for the Tag 1 all-tools `interpret_speech` agent
(US-T1-02).

Not part of the app; used via `make eval-all-tools`. Sits alongside
`tests/integration/agents/catalog/interpret_speech/` rather than replacing
it: the pytest suite is the fast pass/fail CI gate, this is for tracking
quality over time (across prompt or model changes) in the LangSmith UI.
Requires a working `LANGSMITH_API_KEY` (+ `LANGSMITH_WORKSPACE_ID` — see
`.env`, some LangSmith accounts need it sent as the `X-Tenant-Id` header or
every workspace-scoped call 403s even with a valid, fully-permissioned key).

Replaces the old `scripts/eval_interpret_speech.py` (US-GR-03), which tested
the earlier read-only, structured-output (`Interpretation`) agent. The Tag 1
agent has no structured output — it calls tools directly and replies in
free-form Portuguese text — so these evaluators check tool usage and the
resulting real Airtable state instead of `intent`/`target_entity`/
`extracted_fields`. All evaluators are deterministic/structural — exact or
substring matches, no LLM-as-judge.

Three fixture Leads (one each for the read/update/delete examples) avoid
sharing mutable state across examples that `evaluate()` may run concurrently
— e.g. the update example changing `Estado` must never race the read
example asserting a different `Estado` on what would otherwise be the same
record. The create example's target name is never reused as a fixture, so
it can never accidentally resolve to an existing record; the record it
actually creates is discovered by search after the run (its ID isn't known
ahead of time) and queued for cleanup in the same `finally` as the fixtures.
"""

from __future__ import annotations

import uuid
from typing import Any

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolMessage
from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Example, Run

from crmToVoice.agents.catalog.interpret_speech import create_interpret_speech_agent
from crmToVoice.agents.catalog.interpret_speech.prompt import render_system_prompt
from crmToVoice.airtable import leads as airtable_leads
from crmToVoice.airtable.client import get_table

DATASET_NAME = "crmToVoice - interpret_speech (all-tools)"

# Same realistic-data convention as scripts/airtable_manage.py — real
# Portuguese names, not "[eval]"-style synthetic labels. One fixture per
# example that needs an existing record, kept distinct so concurrent
# `evaluate()` runs never step on each other's state.
FIXTURE_READ_LEAD_NOME = "Beatriz Santos"
FIXTURE_UPDATE_LEAD_NOME = "Carlos Mendes"
FIXTURE_DELETE_LEAD_NOME = "Diana Ferreira"
CREATE_LEAD_NOME = "Inês Rodrigues"

# Records this run creates that aren't fixtures (currently just whatever the
# create example produces) — discovered and queued for cleanup by the
# `airtable_state_correct` evaluator, deleted alongside the fixtures.
_dynamic_cleanup: list[tuple[str, str]] = []


def create_airtable_fixtures() -> list[tuple[str, str]]:
    """Creates the real Leads the read/update/delete examples act on.
    Returns `(table_name, record_id)` pairs for `delete_airtable_fixtures`.
    """
    created: list[tuple[str, str]] = []

    read_lead = get_table("Leads").create(
        {"Nome": FIXTURE_READ_LEAD_NOME, "Estado": "Em Negociação"}
    )
    created.append(("Leads", read_lead["id"]))

    update_lead = get_table("Leads").create(
        {"Nome": FIXTURE_UPDATE_LEAD_NOME, "Estado": "Em Negociação"}
    )
    created.append(("Leads", update_lead["id"]))

    delete_lead = get_table("Leads").create({"Nome": FIXTURE_DELETE_LEAD_NOME})
    created.append(("Leads", delete_lead["id"]))

    return created


def delete_airtable_fixtures(created: list[tuple[str, str]]) -> None:
    for table_name, record_id in created:
        try:
            get_table(table_name).delete(record_id)
        except requests.exceptions.HTTPError:
            pass


# One example per docs/backlog/epics/epic-03-tag-1-single-agent.md US-T1-02:
# create, read, update, delete, plus an "unclear utterance" regression check
# carried over from the old suite (cheap, still valuable: nothing should be
# invented for noise). `required_tool_calls`/`forbidden_tool_calls` are
# checked against the ordered list of tool names actually called;
# `airtable_check` tells `airtable_state_correct` what real state to verify.
EXAMPLES: list[dict[str, Any]] = [
    {
        "inputs": {
            "text": (
                f"Novo lead. {CREATE_LEAD_NOME}, telefone 912 345 678, quer um "
                "apartamento de 2 quartos até 250 mil, contacto por referência da Ana."
            )
        },
        "outputs": {
            # `Nome`/`Telefone`/`Tipo de Imóvel Procurado`/`Orçamento`/`Origem` are
            # all present in the utterance (docs/CRM.md's "perguntados se em falta"
            # Lead fields), so the agent has everything it needs to create
            # immediately — nothing should be left for it to ask about first.
            "required_tool_calls": ["search_leads", "create_lead"],
            "forbidden_tool_calls": ["delete_lead", "update_lead"],
            "search_before_create": True,
            "airtable_check": {
                "kind": "create",
                "search_name": CREATE_LEAD_NOME,
                "expected_fields": {
                    "Nome": CREATE_LEAD_NOME,
                    "Orçamento": 250000,
                    "Tipo de Imóvel Procurado": "Apartamento",
                    "Origem": "Referência",
                },
            },
        },
    },
    {
        "inputs": {"text": f"Qual é o estado da {FIXTURE_READ_LEAD_NOME}?"},
        "outputs": {
            "required_tool_calls": ["find_lead"],
            "forbidden_tool_calls": ["create_lead", "update_lead", "delete_lead"],
            "search_before_create": False,
            "airtable_check": {"kind": "none"},
            "reply_contains": "negociação",
        },
    },
    {
        "inputs": {"text": f"O {FIXTURE_UPDATE_LEAD_NOME} já não está interessado."},
        "outputs": {
            "required_tool_calls": ["find_lead", "update_lead"],
            "forbidden_tool_calls": ["create_lead", "delete_lead"],
            "search_before_create": False,
            "airtable_check": {
                "kind": "update",
                "fixture_key": "update_lead_id",
                "expected_fields": {"Estado": "Perdido"},
            },
        },
    },
    {
        "inputs": {"text": f"Apaga o lead da {FIXTURE_DELETE_LEAD_NOME}."},
        "outputs": {
            "required_tool_calls": [],
            "forbidden_tool_calls": ["delete_lead"],
            "search_before_create": False,
            "airtable_check": {
                "kind": "unchanged",
                "fixture_key": "delete_lead_id",
            },
        },
    },
    {
        "inputs": {"text": "Hmm, uh, não sei, esquece."},
        "outputs": {
            "required_tool_calls": [],
            "forbidden_tool_calls": [
                "create_lead",
                "update_lead",
                "delete_lead",
                "create_imovel",
                "update_imovel",
                "delete_imovel",
            ],
            "search_before_create": False,
            "airtable_check": {"kind": "none"},
        },
    },
]

# Populated by `main()` right after fixture creation, keyed by
# `airtable_check.fixture_key` above — evaluators read record IDs from here.
_fixture_ids: dict[str, str] = {}


def ensure_dataset(client: Client) -> None:
    """Fully resyncs the dataset to `EXAMPLES` on every run: deletes every
    existing example first, then recreates from scratch. Only 5 examples,
    fully owned by this script, so a full delete+recreate is cheap and never
    drifts (see the old script's identical rationale — `outputs`' shape has
    changed more than once already).
    """
    if not client.has_dataset(dataset_name=DATASET_NAME):
        client.create_dataset(
            dataset_name=DATASET_NAME,
            description=(
                "Representative create/read/update/delete utterances for the Tag 1 "
                "all-tools interpret_speech agent (US-T1-02)."
            ),
        )
    existing_ids = [ex.id for ex in client.list_examples(dataset_name=DATASET_NAME)]
    if existing_ids:
        client.delete_examples(existing_ids)
    client.create_examples(dataset_name=DATASET_NAME, examples=EXAMPLES)


def target(inputs: dict) -> dict:
    """Runs the real agent for one dataset example. Real OpenRouter call, no
    mocking. The agent no longer bakes in a system prompt (see `agent.py`'s
    docstring) — same as the webhook, this builds a fresh one per call.
    """
    agent = create_interpret_speech_agent()
    result = agent.invoke(
        {
            "messages": [
                {"role": "system", "content": render_system_prompt()},
                {"role": "user", "content": inputs["text"]},
            ]
        },
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
    )

    tool_call_sequence = [
        m.name for m in result["messages"] if isinstance(m, ToolMessage) and m.name
    ]

    reply_text = ""
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage):
            reply_text = str(message.content)
            break

    return {"reply_text": reply_text, "tool_call_sequence": tool_call_sequence}


def _outputs(example: Example) -> dict[str, Any]:
    return example.outputs or {}


def tool_usage_correct(run: Run, example: Example) -> dict:
    expected = _outputs(example)
    actual_sequence = (run.outputs or {}).get("tool_call_sequence") or []
    actual = set(actual_sequence)

    missing = set(expected["required_tool_calls"]) - actual
    unexpected = set(expected["forbidden_tool_calls"]) & actual
    problems = []
    if missing:
        problems.append(f"missing required calls: {sorted(missing)!r}")
    if unexpected:
        problems.append(f"forbidden calls present: {sorted(unexpected)!r}")

    return {
        "key": "tool_usage_correct",
        "score": not problems,
        "comment": "; ".join(problems) if problems else f"ok ({actual_sequence!r})",
    }


def no_duplicate_create(run: Run, example: Example) -> dict:
    """For the create example: a search/find tool call must happen BEFORE
    `create_lead`/`create_imovel`, not just somewhere in the run — otherwise
    a duplicate could already have been created before the check.
    """
    expected = _outputs(example)
    if not expected.get("search_before_create"):
        return {"key": "no_duplicate_create", "score": True, "comment": "not applicable"}

    sequence = (run.outputs or {}).get("tool_call_sequence") or []
    search_tools = {"search_leads", "search_imoveis", "find_lead", "find_imovel"}
    create_tools = {"create_lead", "create_imovel"}

    create_index = next((i for i, name in enumerate(sequence) if name in create_tools), None)
    search_index = next((i for i, name in enumerate(sequence) if name in search_tools), None)

    if create_index is None:
        return {"key": "no_duplicate_create", "score": False, "comment": "no create call found"}
    if search_index is None or search_index > create_index:
        return {
            "key": "no_duplicate_create",
            "score": False,
            "comment": f"no search before create in {sequence!r}",
        }
    return {"key": "no_duplicate_create", "score": True, "comment": f"ok ({sequence!r})"}


def delete_confirmation_required(run: Run, example: Example) -> dict:
    expected = _outputs(example)
    if expected["airtable_check"]["kind"] != "unchanged":
        return {"key": "delete_confirmation_required", "score": True, "comment": "not applicable"}

    sequence = (run.outputs or {}).get("tool_call_sequence") or []
    reply = str((run.outputs or {}).get("reply_text") or "")
    deleted_without_confirmation = "delete_lead" in sequence or "delete_imovel" in sequence
    asked_something = "?" in reply

    problems = []
    if deleted_without_confirmation:
        problems.append("delete_* was called on the first turn, before any confirmation")
    if not asked_something:
        problems.append(f"reply doesn't look like a confirmation question: {reply!r}")

    return {
        "key": "delete_confirmation_required",
        "score": not problems,
        "comment": "; ".join(problems) if problems else "ok",
    }


def reply_mentions_expected_info(run: Run, example: Example) -> dict:
    expected_substring = _outputs(example).get("reply_contains")
    if not expected_substring:
        return {"key": "reply_mentions_expected_info", "score": True, "comment": "not applicable"}

    reply = str((run.outputs or {}).get("reply_text") or "").lower()
    ok = expected_substring.lower() in reply
    return {
        "key": "reply_mentions_expected_info",
        "score": ok,
        "comment": "ok" if ok else f"{expected_substring!r} not found in {reply!r}",
    }


def airtable_state_correct(run: Run, example: Example) -> dict:
    check = _outputs(example)["airtable_check"]
    kind = check["kind"]

    if kind == "none":
        return {"key": "airtable_state_correct", "score": True, "comment": "not applicable"}

    if kind == "create":
        matches = airtable_leads.search_leads(check["search_name"])
        if not matches:
            return {
                "key": "airtable_state_correct",
                "score": False,
                "comment": f"no Lead matching {check['search_name']!r} found in Airtable",
            }
        for match in matches:
            _dynamic_cleanup.append(("Leads", match["id"]))
        record = matches[0]
    elif kind in ("update", "unchanged"):
        record_id = _fixture_ids[check["fixture_key"]]
        try:
            record = airtable_leads.get_lead(record_id)
        except requests.exceptions.HTTPError:
            return {
                "key": "airtable_state_correct",
                "score": False,
                "comment": f"record {record_id!r} no longer exists (was it deleted?)",
            }
    else:
        raise ValueError(f"unknown airtable_check.kind: {kind!r}")

    if kind == "unchanged":
        return {"key": "airtable_state_correct", "score": True, "comment": "record still exists"}

    fields = record["fields"]
    problems = []
    for field_name, expected_value in check["expected_fields"].items():
        actual_value = fields.get(field_name)
        if actual_value != expected_value:
            problems.append(f"{field_name!r}={actual_value!r} != expected {expected_value!r}")

    return {
        "key": "airtable_state_correct",
        "score": not problems,
        "comment": "; ".join(problems) if problems else "ok",
    }


def main() -> None:
    load_dotenv()
    created_fixtures = create_airtable_fixtures()
    _, update_id, delete_id = (record_id for _, record_id in created_fixtures)
    _fixture_ids["update_lead_id"] = update_id
    _fixture_ids["delete_lead_id"] = delete_id

    try:
        client = Client()
        ensure_dataset(client)
        evaluate(
            target,
            data=DATASET_NAME,
            evaluators=[
                tool_usage_correct,
                no_duplicate_create,
                delete_confirmation_required,
                reply_mentions_expected_info,
                airtable_state_correct,
            ],
            experiment_prefix="interpret_speech_all_tools",
            client=client,
            description=(
                "US-T1-02 Tag 1 all-tools interpret_speech agent — "
                "structural/exact-match evaluators against real tool calls "
                "and real Airtable state, no LLM-judge."
            ),
        )
    finally:
        delete_airtable_fixtures(created_fixtures + _dynamic_cleanup)


if __name__ == "__main__":
    main()
