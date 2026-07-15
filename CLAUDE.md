# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Design is complete; implementation proceeds epic-by-epic (`docs/backlog/epics/`, each with checkboxed acceptance criteria):

- **Epic 01 (Database) — done.** `src/crmToVoice/airtable/` (`client.py`, `leads.py`, `imoveis.py`, `visitas.py`): plain create/read/update/delete/search functions over Airtable, no LangChain/agent concerns. See `docs/backlog/epics/epic-01-database.md`.
- **Epic 02 (Agent Foundations) — not started.** `models/` (all Pydantic schemas — `AgentState`, per-entity field models, the `interpret_speech` structured-output schema), `agents/tools/` (wraps `airtable/` for the graph), LLM config. See `docs/backlog/epics/epic-02-agent-foundations.md` and `docs/folder-structure.md`.
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

### Planned agent layering (Epic 02+, not built yet — see `docs/Agent.md`)

- **Package layout** (`src/crmToVoice/`): `graph.py` (StateGraph wiring), `models/` (every Pydantic model — `AgentState`, per-entity field models like `LeadFields`/`PropertyFields`/`VisitFields`, and the `interpret_speech` structured-output schema; not a separate installable package, just a subpackage — this repo is a single `pyproject.toml`, not a multi-package monorepo, see `docs/folder-structure.md`), `config.py` (LLM settings), `webhook.py` (FastAPI adapter), and `agents/` split into `middleware/` (deterministic Context Middleware), `tools/` (wraps `airtable/` for the graph — never talks to `pyairtable` directly), and `catalog/crmAgent/` (the four intent paths — `create.py`, `read.py`, `update.py`, `delete.py`).
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
