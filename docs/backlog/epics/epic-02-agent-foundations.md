# Epic 02 — Agent Foundations

**Status: ✅ Done (2026-07-16).** All three user stories (US-AG-01, US-AG-02,
US-AG-03) complete.

**Goal:** have the shared pieces that every later agent epic (03 —
Minimal graph + Read, 04 — Create, 05 — Update, 06 — Delete) will depend
on: the graph's state schema, the "tools" the nodes will call to talk to
Airtable, and the LLM configuration. None of those epics can move forward
without this first.

**Out of scope for this epic:** the `StateGraph` itself (no node, no
router, no compiled graph — that's Epic 03), any of the four paths
(Create/Read/Update/Delete), the `checkpointer`/`langgraph.json` (already
decided in `docs/Agent.md` §8, but only actually used starting in
Epic 03), and the webhook (Epic 07).

**Depends on:** Epic 01 (`src/crmToVoice/airtable/` — `client.py`,
`leads.py`, `imoveis.py`, `visitas.py`), already done.

---



## US-AG-01 — Pydantic models (`models/`)

As a developer
I want every Pydantic model for the agent centralized in a
`src/crmToVoice/models/` subpackage — `AgentState`, the per-entity field
models, and the LLM's structured-output schema
So that every node in the epics that follow reads/writes the same typed
shapes, instead of each path inventing its own or passing loose `dict`s
around

Note: this is **not** a separate installable package (the project has a
single `pyproject.toml`, it isn't a multi-package monorepo) — it's just a
subpackage of the same `crmToVoice` package, see `docs/folder-structure.md`.

**Status: ✅ Done (2026-07-15).** Implemented in `src/crmToVoice/models/`
(`state.py`, `fields.py`, `interpretation.py`, `__init__.py`), with unit
tests (pure, no I/O) in `tests/unit/models/`. `uv run ruff format --check .`,
`make lint`, `make typecheck`, `make test-unit` all pass: 51 unit tests
(21 new, 30 pre-existing from Epic 01, no regressions).

**Acceptance Criteria:**

- [x] `src/crmToVoice/models/__init__.py` re-exports the public models of
  ```
  the subpackage, so the rest of the code imports from
  `crmToVoice.models` without knowing which file each model lives in
  ```
- [x] `AgentState` (Pydantic `BaseModel`) with the fields from `Agent.md`
  ```
  §4: `session_id`, `current_input`, `intent`, `target_entity`,
  `crm_context`, `extracted_fields`, `skipped_fields`,
  `pending_question`, `awaiting_delete_confirmation`,
  `final_response`
  ```
- [x] Per-entity field models (`LeadFields`, `PropertyFields`,
  ```
  `VisitFields`), typed from the tables in `CRM.md` §1, to replace the
  loose `dict`s that `crm_context`/`extracted_fields` would otherwise
  use
  ```
- [x] Structured-output schema for the `interpret_speech` node
  ```
  (`Agent.md` §9: "structured output" — `intent` + `target_entity` +
  `extracted_fields`), as its own Pydantic model, separate from
  `AgentState`
  ```
- [x] Merge behavior across turns documented and made explicit for the
  ```
  fields on `AgentState` that accumulate (`extracted_fields`,
  `skipped_fields`) — decide whether they use a LangGraph reducer
  (`Annotated[..., operator.add]` or equivalent) or whether the merge
  is done by hand inside the nodes; see the idempotency note in
  `Agent.md` §6 before picking an automatic reducer on a field that
  might be touched before an `interrupt()`
  ```
- [x] Unit test that instantiates `AgentState` with the minimum set of
  ```
  fields and confirms the defaults (`pending_question=None`,
  `awaiting_delete_confirmation=False`, `skipped_fields=[]`)
  ```

---



## US-AG-02 — Agent tools over the Airtable layer

As a developer
I want functions in `agents/tools/` that wrap the functions that already
exist in `airtable/` (`leads.py`, `imoveis.py`, `visitas.py`)
So that the nodes in the paths (Epics 03–06) call an interface designed
for the agent, and never the Airtable API directly

**Acceptance Criteria:**

- [x] One "tool" function per operation the four paths will need directly
  ```
  — mapped 1:1 or aggregated from the functions already built in
  Epic 01, without duplicating business logic (validating required
  fields, wizard rules, etc. stay in the path nodes, not here — this
  layer is only the graph↔data boundary)
  ```
- [x] Covers search by name/address (`search_leads`/`search_imoveis`),
  ```
  already identified in `docs/backlog/epics/epic-01-database.md` as
  used by `interpret_speech`/Router 2's own tool-calling (Epic 03)
  ```
- [x] Unit tests with the Airtable layer mocked (reusing the mocks already
  ```
  used in `tests/unit/airtable/`)
  ```

---



## US-AG-03 — LLM configuration (OpenRouter)

As a developer
I want a single configuration point for the model used by the "Interpret
Speech" node
So that switching models means changing an env var, not code — decision
already made in `2026-07-14-agent-runtime-design.md` §1

**Status: ✅ Done (2026-07-16).** Implemented in `src/crmToVoice/config.py`
(`get_openrouter_model()`, `get_chat_model()`), with unit tests in
`tests/unit/test_config.py`. `make lint`, `uv run ruff format --check .`,
`make typecheck`, `make test-unit` all pass: 83 unit tests (5 new, no
regressions).

**Acceptance Criteria:**

- [x] `config.py` exposes the OpenRouter model to use, read from an
  ```
  environment variable (e.g. `OPENROUTER_MODEL`), with no model value
  hardcoded in any node's code
  ```
- [x] `.env.example` updated with the new variable
  ```
  (already present from an earlier pass — `OPENROUTER_API_KEY` and
  `OPENROUTER_MODEL` were both already there, unused until now)
  ```
- [x] A reusable chat-model client/wrapper — so it isn't reimplemented in
  ```
  every node that needs an LLM (today just `interpret_speech`, but
  potentially `read_format_response` too in Epic 03)
  ```
  ```
  `get_chat_model()` is an `lru_cache`d factory returning a `ChatOpenAI`
  instance pointed at OpenRouter's base URL (`langchain_openai.ChatOpenAI`
  is OpenAI-API-compatible, which is what OpenRouter exposes) — mirrors
  the `airtable/client.py::get_api()` caching pattern from Epic 01.
  ```

---



## Open notes for review

- `TypedDict` ~~vs~~ `dataclass` ~~vs Pydantic for~~ `AgentState` — resolved:
Pydantic, for every model in `models/` (see US-AG-01 and
`docs/folder-structure.md`).
- No story here covers actual LLM calls in a graph context — only
configuration/client. The first real use of `interpret_speech` is in
Epic 03.
- Whether `agents/tools/` should expose one function per table
(Lead/Property/Visit) or per cross-cutting action (e.g. "resolve a name
mention") isn't settled yet — to decide while writing the code, but
name/address search and disambiguation itself belongs to Router 2
(`interpret_speech`)'s own tool-calling (Epic 03), not this epic.

