# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Design is complete; implementation proceeds epic-by-epic (`docs/backlog/epics/`, each with checkboxed acceptance criteria):

- **Epic 01 (Database) — done.** `src/crmToVoice/airtable/` (`client.py`, `leads.py`, `imoveis.py`, `visitas.py`): plain create/read/update/delete/search functions over Airtable, no LangChain/agent concerns. See `docs/backlog/epics/epic-01-database.md`.
- **Epic 02 (Agent Foundations) — in progress.** `src/crmToVoice/models/` (`state.py`, `fields.py`, `interpretation.py`) is done (US-AG-01): `AgentState`, per-entity field models (`LeadFields`/`PropertyFields`/`VisitFields`), and the `Interpretation` structured-output schema for the future `interpret_speech` node. `src/crmToVoice/agents/tools/` is also done (US-AG-02): `@tool`-decorated 1:1 passthrough wrappers over the Epic 01 functions, so graph nodes never call `pyairtable`/`airtable/` directly. Still not started: `config.py` (OpenRouter LLM config, US-AG-03). See `docs/backlog/epics/epic-02-agent-foundations.md` and `docs/folder-structure.md`.
- Everything past that (the actual `StateGraph`, the four intent paths, the webhook) is further out. `src/crmToVoice/graph.py` and `src/webhook.py` currently exist as empty stub files — note `src/webhook.py` is *not* the path `Dockerfile.webhook`/the architecture expect (`crmToVoice.webhook:app`, i.e. `src/crmToVoice/webhook.py`); don't assume the stray top-level one is meaningful.

The design docs under `docs/` are authoritative and should be read before writing any code:

- `docs/CRM.md` — Airtable data model (Leads, Imóveis/Properties, Visitas/Visits tables, field lists) and the full catalog of voice-driven CRM actions (Create/Read/Update/Delete), including the field-classification rules (which fields are auto-filled vs. asked-if-missing) and the guided-wizard question mechanics.
- `docs/Agent.md` — the LangGraph agent design: session/memory model, the middleware/agent layering, the shared `AgentState`, the two-router four-path graph, the `interrupt()`-based pause/resume mechanism (including the idempotency constraint in §6), error/fallback handling, a node-to-file mapping (§9), and a Mermaid diagram of the full graph.
- `docs/superpowers/specs/2026-07-14-agent-runtime-design.md` — runtime decisions: LLM via OpenRouter (model left as a swappable config value), local-only hosting via `langgraph dev` + a thin FastAPI webhook adapter in front of it (no production deploy yet), SQLite checkpointer, and the exact Shortcut↔webhook JSON payload (`{session_id, text}` → `{session_id, reply_text, done}`).
- `docs/siri-shortcut-integration.md` — factual reference for the iPhone Shortcut side (voice trigger, dictation, the `Get Contents of URL`/JSON webhook call, response parsing, the multi-turn loop pattern), with items still needing hands-on verification called out explicitly (notably: whether plain `http://` to a LAN IP actually works from the Shortcuts app).
- `docs/folder-structure.md` — full repository layout (built vs. planned), and why `models/` is a subpackage rather than a separate installable package.

## Commands

Package manager is **uv**; all commands are also exposed as `make` targets (`make help` lists them).

```
make setup - uv sync — creates .venv, installs everything
make dev - uv run langgraph dev (graph key "crmAgent"; won't actually start until graph.py defines `graph`)
make lint - uv run ruff check .
make format - uv run ruff format .
make typecheck - uv run pyright
make test-unit - uv run pytest tests/unit — mocked, no credentials needed
make test-integration - uv run pytest tests/integration — hits real Airtable/OpenRouter
make test - both of the above
make check - lint + typecheck + test
```

Run a single test: `uv run pytest tests/unit/airtable/test_leads.py::test_create_lead_passes_fields_through -v` (or the equivalent path under `tests/integration/`).

Integration tests need `AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID` (and `OPENROUTER_API_KEY` once the agent exists). Locally, `tests/integration/conftest.py` auto-loads `.env` via `python-dotenv`, so `uv run pytest tests/integration` just works without manually sourcing anything; it never overrides real env vars, so CI (which injects them as GitHub Actions secrets, no `.env` file present) is unaffected. There is no sandbox Airtable base — integration tests run against the real one and must clean up what they create.

Local multi-service run: `docker compose up` builds `Dockerfile.langgraph` (the `graph` service, port 2024) and `Dockerfile.webhook` (the `webhook` service, port 8000, talks to `graph` via `LANGGRAPH_API_URL=http://graph:2024`, running `crmToVoice.webhook:app`). Requires a populated `.env` (see `.env.example`); neither service is functional yet since `graph.py`/`webhook.py` are still empty.

## Git workflow

`main` is branch-protected on GitHub: `quality`, `integration`, and `docker-build` CI checks must pass before anything lands (`enforce_admins: true`, so this applies even to the repo owner). **Direct pushes to `main` are rejected** — use a feature branch + PR, even for small changes.

## Architecture

### Airtable data-access layer (`src/crmToVoice/airtable/`, done — Epic 01)

- Single cached connection: `client.get_api()` (`lru_cache`d `pyairtable.Api` from `AIRTABLE_API_KEY`) and `client.get_table(name)` (uses `AIRTABLE_BASE_ID`). Every repo function (`leads.py`/`imoveis.py`/`visitas.py`) goes through these — none instantiate `pyairtable` directly.
- `client.get_records_by_ids(table, ids)` is the generic multi-get used by `leads.get_lead`/`imoveis.get_imovel` to expand their linked `Visitas` field into full records (adding a `"visitas"` key, leaving `fields.Visitas`'s raw ID list untouched).
- Search (`leads.search_leads`, `imoveis.search_imoveis`) uses `pyairtable.formulas` (`SEARCH(LOWER(...), LOWER(...))`) for case-insensitive partial matching server-side.
- `visitas.list_visitas_by_lead` can't filter by a server-side formula on the linked record's ID — Airtable formulas evaluate a linked-record field to the *linked record's primary-field text*, not its record ID. It fetches all Visitas and filters client-side by membership instead (accepted tradeoff; no pagination).
- `visitas.create_visita` is the one place with input validation in this layer: raises `ValueError` if `fields["Lead"]` is missing/empty (a Visita must always link to a Lead). Everything else across all three repos is a thin passthrough — field validation, API error handling, and pagination are explicitly out of scope for Epic 01 (see the epic's "Open notes for review").
- Airtable quirk worth knowing: fetching a deleted record raises `requests.exceptions.HTTPError` from a **403**, not a 404.
- Unit tests mock at `patch.object(<module>, "get_table", ...)`; integration tests hit the real base and use a `cleanup` fixture (register created record → delete in teardown) since there's no sandbox base.
- Note on naming: `imoveis.py`/`visitas.py` and their function/parameter names (`create_imovel`, `search_leads(nome)`, etc.) use Portuguese entity names because that's what Epic 01 was actually written and tested against — renaming them is a source-code refactor of shipped, CI-passing work, tracked separately rather than done as a docs-only change.

### Pydantic models (`src/crmToVoice/models/`, done — Epic 02 US-AG-01)

- `AgentState` (`state.py`) is a plain Pydantic `BaseModel`, not yet wired into a `StateGraph`. `Intent`/`TargetEntity` are `Literal` type aliases (not `Enum`), reused verbatim by `interpretation.py` — don't redefine equivalent literals elsewhere.
- Deliberate non-decision to remember: no automatic LangGraph reducer (e.g. `Annotated[dict, operator.or_]`) on `extracted_fields`/`skipped_fields`, even once this becomes real `StateGraph` state. Reasoning ties back to the idempotency-before-`interrupt()` constraint below — an automatic additive reducer would double-apply a merge every time a node re-runs before its *next* `interrupt()` resolves. Merging across turns must be explicit, node-owned logic instead.
- `Interpretation` (`interpretation.py`) is the future `interpret_speech` LLM node's structured-output contract — deliberately separate from `AgentState` (the LLM's per-call output, not the graph's running state) and keeps `extracted_fields` as a generic `dict`, since `target_entity` (which would determine the field shape) is itself part of the same structured output.
- `LeadFields`/`PropertyFields`/`VisitFields` (`fields.py`) represent a possibly-partial record accumulated across wizard turns, not a guaranteed-complete Airtable row. Every field has both a Python attribute name and an Airtable-literal alias (`validation_alias`/`serialization_alias`, with `populate_by_name=True`); callers must dump with `.model_dump(by_alias=True, exclude_none=True)` — never the bare `.model_dump()` — to get Airtable-ready dicts for `create_*`/`update_*` in the Epic 01 layer.

### Agent tools (`src/crmToVoice/agents/tools/`, done — Epic 02 US-AG-02)

- One file per table (`leads.py`, `imoveis.py`, `visitas.py`), mirroring `airtable/`'s split — 16 functions total, each decorated with `@tool` from `langchain_core.tools` and a pure 1:1 passthrough to the matching Epic 01 function (same params, same return value). No validation, wizard logic, or find-or-create behavior lives here — that stays in the path nodes (Epics 03-06).
- Being `@tool`-decorated, callers invoke them as LangChain tools, not plain functions — e.g. `create_lead.invoke({"fields": {...}})`, not `create_lead({...})`. This also means every tool needs a non-empty docstring (required as the tool's `description` — `@tool` raises at decoration time without one) and gets an inferred Pydantic arg schema that validates input types before the call reaches Airtable.
- `__init__.py` re-exports every tool, so callers import from `crmToVoice.agents.tools` without knowing which file a tool lives in.
- `search_leads`/`search_imoveis` are included even though nothing in this epic calls them — they're for the future Context Middleware (Epic 03) to resolve name/address mentions before the LLM runs.
- `tests/unit/agents/tools/` mocks the underlying `airtable/` function directly (not `get_table`) and asserts via `.invoke()`. Note: this test directory shares basenames with `tests/unit/airtable/` (`test_leads.py` etc.), which collided under pytest's default import mode since neither has `__init__.py` — fixed via `--import-mode=importlib` in `pyproject.toml`; don't remove that setting or re-add per-directory `__init__.py` files as an alternative fix without checking why importlib mode was chosen.

### Planned agent layering (Epic 03+, not built yet — see `docs/Agent.md`)

- **Package layout** (`src/crmToVoice/`, still to build): `graph.py` (StateGraph wiring), `config.py` (LLM settings), `webhook.py` (FastAPI adapter), and `agents/` split into `middleware/` (deterministic Context Middleware) and `catalog/crmAgent/` (the four intent paths — `create.py`, `read.py`, `update.py`, `delete.py`). `models/` and `agents/tools/` (both done, see above) are not separate installable packages, just subpackages — this repo is a single `pyproject.toml`, not a multi-package monorepo, see `docs/folder-structure.md`.
- **CRM backend**: Airtable base "CRM Imobiliário (Voz)" (base ID `appiFiRN7rzTMqyff`, workspace "Porjeto" — literal external names, not translated), three linked tables: Leads, Imóveis (Properties), Visitas (Visits).
- **Session model**: each Shortcut execution ("Hey Siri...") is an isolated thread/session (`session_id` = `thread_id`). Short-term memory within a session is the LangGraph checkpointer only — no memory across separate sessions; the Airtable CRM itself is the long-term memory (look up by name, don't recall past conversations). Interrupted sessions are discarded, not resumed — nothing is written to Airtable until an action is complete/confirmed.
- **Layering**: the deterministic Context Middleware resolves any Lead/Property named in the incoming text against Airtable *before* the LLM reasoning runs, so the agent never queries Airtable to search — it only writes (create/update/delete) or reads (query) at the end of a path.
- **Graph shape**: two routers, four paths.
  - Router 1 (deterministic): is this session mid-wizard/mid-confirmation (a `pending_question` exists)? If so, skip re-classification and resume the active path.
  - Router 2 (LLM-classified on a fresh turn): routes to one of **Create / Read / Update / Delete**.
  - **Create** is the only path with the missing-field wizard (asks only for fields the person didn't already mention, grouped by topic, accepts "I don't know"/"skip").
  - **Update** never asks for extra fields — except changing a Lead's `Estado` (Status), which triggers a "why?" follow-up and creates a linked Visit (Note) recording the reason, rather than a bare field update.
  - **Delete** always requires explicit voice confirmation before deleting; no confirmation = no delete.
  - **Read** never writes; if the referenced Lead/Property isn't found, it says so rather than guessing.
- **Implementation constraint to remember when building these paths**: a node can call `interrupt()` more than once within the same path (the wizard's follow-up questions per `CRM.md` §4 rule 2), and everything *before* an `interrupt()` re-runs from scratch on resume — that's how LangGraph works. No Airtable write (create/update/delete) may happen before the *last* `interrupt()` in a path resolves, or a wizard follow-up would re-trigger it (e.g. duplicate Lead creation). The Context Middleware (`resolve_context`) must stay read-only for the same reason.

## Product summary

Field real-estate agents don't log visits/leads in the CRM because typing is friction. The fix: the agent speaks to Siri ("Hey Siri, log visit..."), an iPhone Shortcut sends the already-dictated text to a webhook, and a LangGraph agent turns that into structured Airtable CRM writes (or, for questions, reads the CRM and returns a spoken answer). The interaction is bidirectional and can be multi-turn (a guided wizard asks only for missing fields, grouped by topic) within a single Shortcut execution.
