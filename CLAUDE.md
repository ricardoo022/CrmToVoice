# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project status

Design has evolved from the original multi-node architecture to a simpler
**Tag 1 (Single Agent) → Tag 2 (Multi-Node Graph)** approach:

- **Epic 01 (Database) — done.** `src/crmToVoice/airtable/` (`client.py`, `leads.py`, `imoveis.py`, `visitas.py`): plain create/read/update/delete/search functions over Airtable, no LangChain/agent concerns. See `docs/backlog/epics/epic-01-database.md`.
- **Epic 02 (Agent Foundations) — done.** `src/crmToVoice/agents/tools/` (US-AG-02): 18 `@tool`-decorated 1:1 wrappers over the Epic 01 functions. `config.py` (US-AG-03): `get_openrouter_model()` + `get_chat_model()` factory. `models/` (US-AG-01): `AgentState`, `LeadFields`/`PropertyFields`/`VisitFields`, `Interpretation` — built for the original architecture, available for Tag 2. See `docs/backlog/epics/epic-02-agent-foundations.md`.
- **Epic 03 (Tag 1 — Single All-Tools Agent MVP) — in progress.** A single `create_agent` with all 18 tools (read + write), no StateGraph, no `interrupt()`, no wizard. Decides autonomously what to do and returns a text reply. See `docs/backlog/epics/epic-03-tag-1-single-agent.md`.
- **Epic 04 (Tag 1 — Siri Integration) — not started.** Wires the Epic 03 agent to the outside world: a FastAPI webhook (`POST /webhook`) and the iPhone Shortcut. Pure wiring, no new agent logic — this is the first deliverable, something a real estate agent can actually use. See `docs/backlog/epics/epic-04-siri-integration.md`.
- **Tag 2 (future)** — the original multi-node StateGraph architecture with separate router (read-only tools), intent paths (write tools), `interrupt()`-based confirmation and wizard, and structured `Interpretation` output. This is the long-term design and remains documented in `docs/Agent.md` (Tag 2 section) and preserved in git history.

The design docs under `docs/` are authoritative and should be read before writing any code:

- `docs/CRM.md` — Airtable data model (Leads, Imóveis/Properties, Visitas/Visits tables, field lists) and the full catalog of voice-driven CRM actions (Create/Read/Update/Delete), including the field-classification rules.
- `docs/Agent.md` — the agent design: Tag 1 single-agent approach (current), Tag 2 vision (future), session model, webhook contract, error handling.
- `docs/siri-shortcut-integration.md` — factual reference for the iPhone Shortcut side (voice trigger, dictation, the `Get Contents of URL`/JSON webhook call, response parsing).
- `docs/folder-structure.md` — full repository layout (built vs. planned).
- `docs/backlog/epics/epic-03-tag-1-single-agent.md` — Tag 1 agent user stories and acceptance criteria.
- `docs/backlog/epics/epic-04-siri-integration.md` — Tag 1 webhook/Siri user stories and acceptance criteria.

## Commands

Package manager is **uv**; all commands are also exposed as `make` targets (`make help` lists them).

```
make setup - uv sync — creates .venv, installs everything
make dev - uv run uvicorn crmToVoice.webhook:app --reload (Tag 1)
make lint - uv run ruff check .
make format - uv run ruff format .
make typecheck - uv run pyright
make test-unit - uv run pytest tests/unit — mocked, no credentials needed
make test-integration - uv run pytest tests/integration — hits real Airtable/OpenRouter
make test - both of the above
make check - lint + typecheck + test
make eval-all-tools - uv run python scripts/eval_all_tools_agent.py — LangSmith eval suite for the Tag 1 all-tools agent
```

Run a single test: `uv run pytest tests/unit/airtable/test_leads.py::test_create_lead_passes_fields_through -v` (or the equivalent path under `tests/integration/`).

Integration tests need `AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID` and `OPENROUTER_API_KEY`. Locally, `tests/integration/conftest.py` auto-loads `.env` via `python-dotenv`, so `uv run pytest tests/integration` just works without manually sourcing anything; it never overrides real env vars, so CI (which injects them as GitHub Actions secrets, no `.env` file present) is unaffected. There is no sandbox Airtable base — integration tests run against the real one and must clean up what they create.

LangSmith calls (tracing, and `make eval-all-tools`) additionally need `LANGSMITH_WORKSPACE_ID` set.

Local run: `docker compose up` builds `Dockerfile.webhook` (the `webhook` service, port 8000). Requires a populated `.env` (see `.env.example`).

## Git workflow

`main` is branch-protected on GitHub. **Direct pushes to `main` are rejected** — use a feature branch + PR, even for small changes.

## Architecture

### Airtable data-access layer (`src/crmToVoice/airtable/`, done — Epic 01)

- Single cached connection: `client.get_api()` (`lru_cache`d `pyairtable.Api` from `AIRTABLE_API_KEY`) and `client.get_table(name)` (uses `AIRTABLE_BASE_ID`). Every repo function (`leads.py`/`imoveis.py`/`visitas.py`) goes through these — none instantiate `pyairtable` directly.
- `client.get_records_by_ids(table, ids)` is the generic multi-get used by `leads.get_lead`/`imoveis.get_imovel` to expand their linked `Visitas` field into full records (adding a `"visitas"` key, leaving `fields.Visitas`'s raw ID list untouched).
- Search (`leads.search_leads`, `imoveis.search_imoveis`) uses `pyairtable.formulas` (`SEARCH(LOWER(...), LOWER(...))`) for case-insensitive partial matching server-side.
- `visitas.list_visitas_by_lead` can't filter by a server-side formula on the linked record's ID — fetches all Visitas and filters client-side by membership instead (accepted tradeoff; no pagination).
- `visitas.create_visita` is the one place with input validation: raises `ValueError` if `fields["Lead"]` is missing/empty.
- Airtable quirk: fetching a deleted record raises `requests.exceptions.HTTPError` from a **403**, not a 404.
- Unit tests mock at `patch.object(<module>, "get_table", ...)`; integration tests use a `cleanup` fixture.

### Agent tools (`src/crmToVoice/agents/tools/`, done — Epic 02 US-AG-02)

- 18 functions total, each decorated with `@tool` from `langchain_core.tools` and a pure 1:1 passthrough to the matching Epic 01 function.
- `__init__.py` re-exports every tool, so callers import from `crmToVoice.agents.tools` without knowing which file a tool lives in.

### Tag 1 single-agent flow (`src/crmToVoice/agents/catalog/interpret_speech/`, Epic 03)

- `agent.py`'s `create_interpret_speech_agent()` now binds **all** 18 tools (read + write), not just the read-only subset.
- No `response_format` — the agent responds with free-form text.
- `prompt.py` is updated to instruct the agent on safe write-tool usage (search before create, confirm before delete, ask for missing fields).
- No StateGraph, no `interrupt()`, no wizard.

### Tag 1 Siri integration (`src/crmToVoice/webhook.py`, Epic 04)

- The webhook creates the Epic 03 agent once (cached), builds a message list with system prompt + user text, invokes, and returns the reply.
- Pure wiring on top of the finished agent — no agent logic lives here.

### Tag 2 (future)

The original multi-node design is preserved in `docs/Agent.md` (Tag 2 section) and in git history. Key differences from Tag 1:
- StateGraph with separate router (read-only tools) + intent paths (write tools)
- `interrupt()`-based confirmation (delete) and wizard (create)
- Structured `Interpretation` output via `response_format`
- `graph.py` wires `add_node`/`add_edge`/`add_conditional_edges`

## Product summary

Field real-estate agents don't log visits/leads in the CRM because typing is friction. The fix: the agent speaks to Siri ("Hey Siri, log visit..."), an iPhone Shortcut sends the already-dictated text to a webhook, and a LangChain agent turns that into structured Airtable CRM writes (or, for questions, reads the CRM and returns a spoken answer). Tag 1 is single-turn; Tag 2 adds multi-turn wizard and confirmation.
