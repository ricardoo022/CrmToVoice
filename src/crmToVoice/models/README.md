# models

**Epic 02, done.** Every Pydantic model used by the agent, in one place. Not a separate installable package: this
repo is a single `pyproject.toml`, not a multi-package monorepo, so this is just a subpackage of
`crmToVoice`. See `docs/folder-structure.md` for the reasoning.

| File | Purpose |
|---|---|
| `__init__.py` | Re-exports the public models so the rest of the code imports from `crmToVoice.models`, not from each file directly. |
| `state.py` | `AgentState` — the shared LangGraph state (`docs/Agent.md` §4), plus the `Intent`/`TargetEntity` `Literal` type aliases. Documents the reducer decision for `extracted_fields`/`skipped_fields` (no automatic LangGraph reducer — see `docs/Agent.md` §6 idempotency-before-`interrupt()` note). |
| `fields.py` | `LeadFields`, `PropertyFields`, `VisitFields` — typed, possibly-partial field sets per entity, from `docs/CRM.md` §1, aliased to the literal Airtable field names so `.model_dump(by_alias=True, exclude_none=True)` feeds directly into `crmToVoice.airtable`'s `create_*`/`update_*` functions. |
| `interpretation.py` | `Interpretation` — the structured-output schema the `interpret_speech` LLM node returns (`intent` + `target_entity` + `extracted_fields`), separate from `AgentState` itself. |

Not yet built (later epics): the `StateGraph`/nodes that actually construct
and mutate these models (Epic 03+).
