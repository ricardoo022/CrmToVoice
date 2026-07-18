# models

**Epic 02, done — but reserved for Tag 2, not used by the current Tag 1 agent.** Every Pydantic
model built for the original multi-node design, in one place. The Tag 1 `interpret_speech` agent
(`agents/catalog/`) replies with free-form text and doesn't construct or return any of these —
they're kept for when Tag 2's `StateGraph` is built. Not a separate installable package: this repo
is a single `pyproject.toml`, not a multi-package monorepo, so this is just a subpackage of
`crmToVoice`. See `docs/folder-structure.md` for the reasoning.

| File | Purpose |
|---|---|
| `__init__.py` | Re-exports the public models so the rest of the code imports from `crmToVoice.models`, not from each file directly. |
| `state.py` | `AgentState` — the shared graph state Tag 2's `StateGraph` will use (`docs/Agent.md`, Tag 2 section), plus the `Intent`/`TargetEntity` `Literal` type aliases. Documents the reducer decision for `extracted_fields`/`skipped_fields` (no automatic reducer — see the Tag 2 idempotency-before-`interrupt()` note). |
| `fields.py` | `LeadFields`, `PropertyFields`, `VisitFields` — typed, possibly-partial field sets per entity, from `docs/CRM.md` §1, aliased to the literal Airtable field names so `.model_dump(by_alias=True, exclude_none=True)` feeds directly into `crmToVoice.airtable`'s `create_*`/`update_*` functions. |
| `interpretation.py` | `Interpretation` — the structured-output schema a Tag 2 router node would return (`intent` + `target_entity` + `extracted_fields`), separate from `AgentState` itself. |

Not yet built: the Tag 2 `StateGraph`/nodes that would actually construct and mutate these models.
