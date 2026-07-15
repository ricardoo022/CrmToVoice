"""Shared LangGraph state for the crmToVoice agent.

Design rationale:

- Only `session_id`/`current_input` are required. Everything else is unknown
  at construction time on a fresh session — `intent`/`target_entity` aren't
  set until the (not-yet-built) `interpret_speech` LLM node runs, which per
  `docs/Agent.md` §9 "only runs on a new session".
- `Intent`/`TargetEntity` are `Literal` type aliases, not `Enum`: they
  reproduce the exact string values used throughout `docs/Agent.md` verbatim,
  need no `.value` unwrapping in future node code, and produce a clean
  JSON-schema `enum` for LLM structured output. These two aliases will be
  imported and reused by `interpretation.py` (built by a parallel
  workstream) — do not redefine them elsewhere.
- **Reducer decision** — no automatic LangGraph reducer (e.g.
  `Annotated[dict, operator.or_]` / `Annotated[list, operator.add]`) on
  `extracted_fields` or `skipped_fields`. `AgentState` is a plain Pydantic
  `BaseModel` today, not yet wired into a `StateGraph` — but record this now
  so a later epic doesn't reach for a reducer reflexively. Reasoning (from
  `docs/Agent.md` §6, the idempotency-before-`interrupt()` rule): all code
  before an `interrupt()` call re-runs from scratch on resume, and a single
  node can call `interrupt()` more than once within the same path (the
  wizard's follow-up questions, `docs/CRM.md` §4 rule 2: "if the answer only
  covers part of the group, ask a follow-up only for the field still
  missing"). An automatic additive reducer on `extracted_fields`/
  `skipped_fields` would double-apply whatever a node merged on an earlier
  pass, every time that node re-executes before its *next* `interrupt()`
  resolves — e.g. appending the same skipped field twice, or re-merging a
  stale partial answer over a newer one. Merging across turns must instead
  be explicit, node-owned logic that knows exactly what the *current* turn's
  answer maps to, run once per turn — not an automatic per-invocation
  accumulator.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

Intent = Literal["create", "read", "update", "delete"]
TargetEntity = Literal["Lead", "Visit", "Property"]


class AgentState(BaseModel):
    session_id: str
    current_input: str
    intent: Intent | None = None
    target_entity: TargetEntity | None = None
    crm_context: dict[str, Any] = Field(default_factory=dict)
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    skipped_fields: list[str] = Field(default_factory=list)
    pending_question: str | None = None
    awaiting_delete_confirmation: bool = False
    final_response: str | None = None
