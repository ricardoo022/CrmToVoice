"""Shared LangGraph state for the crmToVoice agent.

Design rationale:

- Only `session_id`/`current_input` are required. Everything else is unknown
  at construction time on a fresh session — `intent`/`target_entity` aren't
  set until the (not-yet-built) `interpret_speech` LLM node runs, which per
  `docs/Agent.md` §9 runs on every turn (new or continuing a session).
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
    # Session/thread identifier — one per Shortcut execution, doubles as the
    # LangGraph `thread_id`. Short-term memory lives only within a session
    # (checkpointer); there is no cross-session memory.
    session_id: str

    # Raw dictated text for the current turn, as received from the webhook.
    # Overwritten every turn; `interpret_speech` reads this fresh each time
    # it runs (which is every turn, new or resumed — see docs/Agent.md §9).
    current_input: str

    # Classification produced by `interpret_speech`: which of the four
    # action paths (Create/Read/Update/Delete) this turn belongs to. `None`
    # until that node has run at least once.
    intent: Intent | None = None

    # Which CRM entity (Lead/Visit/Property) the intent applies to, also
    # produced by `interpret_speech`. Determines which of
    # LeadFields/VisitFields/PropertyFields shapes `extracted_fields`.
    target_entity: TargetEntity | None = None

    # Existing Airtable record(s) resolved via the read-only search tools
    # when `interpret_speech` (Router 2) decides the input mentions a known
    # Lead/Property. Populated by that LLM agent itself, not by a separate
    # deterministic lookup step.
    crm_context: dict[str, Any] = Field(default_factory=dict)

    # Field values gathered so far for the current create/update wizard,
    # keyed by the Airtable-literal names used in `models/fields.py`. Merged
    # explicitly by node-owned logic each turn — no automatic reducer (see
    # module docstring for why).
    extracted_fields: dict[str, Any] = Field(default_factory=dict)

    # Fields the caller explicitly said "I don't know"/"skip" for, so the
    # wizard doesn't re-ask them. Same manual-merge caveat as
    # `extracted_fields`.
    skipped_fields: list[str] = Field(default_factory=list)

    # The question currently awaiting an answer via `interrupt()`, if any.
    # Non-None tells interpret_speech/Router 2 — the single entry point —
    # this turn is a resume of a mid-wizard/mid-confirmation session rather
    # than a fresh request.
    pending_question: str | None = None

    # Set by the Delete path right before its confirmation `interrupt()`.
    # Must be True for a "yes" reply to actually trigger the delete — no
    # confirmation, no delete.
    awaiting_delete_confirmation: bool = False

    # The spoken/text reply to send back through the webhook once this
    # turn's processing is done. Read by the webhook adapter, not by any
    # downstream graph node.
    final_response: str | None = None
