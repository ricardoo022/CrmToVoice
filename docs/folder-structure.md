# Folder structure

This is a **single-package repository**, not a multi-package monorepo: one
`pyproject.toml`, one `uv.lock`, one Python dependency graph. The two Docker
images (`Dockerfile.langgraph`, `Dockerfile.webhook`) both `uv sync` the same
lockfile and just run a different entrypoint (`langgraph dev` vs
`uvicorn crmToVoice.webhook:app`) — they are not separately-versioned
packages, so there is no need for the "extract shared types into their own
installable package" pattern that monorepos use. Anything shared between
the two just lives in the one `crmToVoice` package and gets imported
directly.

Legend: ✅ built · 🔲 planned (README-only stub today)

```
CrmToVoice/
├── docs/                              — design docs, authoritative; read before writing code
│   ├── CRM.md                         — Airtable data model + voice-action catalog (Create/Read/Update/Delete)
│   ├── Agent.md                       — LangGraph agent design: AgentState, graph shape, interrupt()/resume, node-to-file map (§9)
│   ├── siri-shortcut-integration.md   — iPhone Shortcut side (dictation, webhook call, response parsing)
│   ├── folder-structure.md            — this file
│   ├── superpowers/specs/
│   │   └── 2026-07-14-agent-runtime-design.md   — runtime decisions (LLM, hosting, checkpointer, payload) + epic sequencing
│   └── backlog/epics/                 — one file per epic, checkboxed acceptance criteria
│       ├── epic-01-database.md        — ✅ done
│       └── epic-02-agent-foundations.md — 🔲 next up
│
├── src/
│   ├── webhook.py                     — ⚠️ stray empty stub, NOT the real one — ignore it. The actual
│   │                                     webhook lives at `src/crmToVoice/webhook.py` (`crmToVoice.webhook:app`,
│   │                                     what `Dockerfile.webhook` actually runs)
│   └── crmToVoice/                    — the one installable package
│       ├── __init__.py
│       ├── graph.py                   — 🔲 StateGraph wiring (compiles the graph `langgraph.json` points at)
│       ├── config.py                  — 🔲 settings (OpenRouter model, etc.), read from env
│       ├── webhook.py                 — 🔲 FastAPI adapter; exposes `POST /webhook` matching the Shortcut's
│       │                                 `{session_id, text}` → `{session_id, reply_text, done}` contract;
│       │                                 talks to `langgraph dev`'s own API internally
│       │
│       ├── models/                    — 🔲 Epic 02 — every Pydantic model, one subpackage, no separate pyproject.toml
│       │   ├── __init__.py            —   re-exports the public models
│       │   ├── state.py               —   `AgentState` (the shared graph state, Agent.md §4)
│       │   ├── fields.py              —   `LeadFields` / `PropertyFields` / `VisitFields` (typed field sets, CRM.md §1)
│       │   └── interpretation.py      —   structured-output schema for the `interpret_speech` LLM node
│       │
│       ├── airtable/                  — ✅ Epic 01 — plain data-access layer, no LangChain/agent concerns
│       │   ├── client.py              —   cached `pyairtable` connection (`get_api()`, `get_table()`)
│       │   ├── leads.py               —   create/read/update/delete/search over Leads
│       │   ├── imoveis.py             —   create/read/update/delete/search over Imóveis (Properties) — module/function
│       │   │                             names stay Portuguese, matching the live Airtable table; see note below
│       │   └── visitas.py             —   create/read/update/delete/query over Visitas (Visits) — same note
│       │
│       └── agents/                    — 🔲 Epic 02+ — the graph's nodes, split by role
│           ├── middleware/            —   deterministic Context Middleware: resolves Lead/Property mentions
│           │                             against Airtable *before* the LLM runs; read-only, uses
│           │                             `airtable/leads.py::search_leads` + `airtable/imoveis.py::search_imoveis`
│           ├── tools/                 —   wraps `airtable/` as the graph's write/read boundary — used only
│           │                             at the *end* of a path (create/update/delete/query), never to search
│           └── catalog/
│               └── crmAgent/          —   the four intent paths (Agent.md §5)
│                   ├── create.py      —     the only path with the missing-field wizard
│                   ├── read.py        —     read-only, never writes
│                   ├── update.py      —     direct field updates, except `Estado`/Status (asks "why?" first)
│                   └── delete.py      —     always requires explicit confirmation before deleting
│
├── tests/
│   ├── unit/                          — external services mocked/faked, fast, no credentials
│   │   └── airtable/                  — ✅ mocks `get_table`/`get_records_by_ids` via `patch.object`
│   └── integration/                   — hits real Airtable/OpenRouter; runs locally and in CI
│       ├── conftest.py                — auto-loads `.env` locally, never overrides real env vars (CI-safe)
│       └── airtable/                  — ✅ real Airtable base, cleans up every record it creates
│
├── db/                                — 🔲 holds the SQLite checkpointer file at runtime (local dev only);
│                                          not source, only appears once the agent has actually run
│
├── langgraph.json                     — points `langgraph dev` at `graph.py:graph`; also where the
│                                          checkpointer factory gets wired in (see the runtime spec §3) —
│                                          `langgraph dev` ignores `compile(checkpointer=...)`, so this file
│                                          is the actual place a custom checkpointer gets configured
├── docker-compose.yml                 — `graph` (port 2024) + `webhook` (port 8000) services
├── Dockerfile.langgraph               — runs `langgraph dev`
├── Dockerfile.webhook                 — runs `uvicorn crmToVoice.webhook:app`
├── pyproject.toml                     — the one and only package definition (name: `crmtovoice`)
├── uv.lock
├── Makefile                           — `make setup|dev|lint|format|typecheck|test-unit|test-integration|test|check`
└── CLAUDE.md                          — instructions for Claude Code working in this repo
```

## Why `models/` isn't its own package

A monorepo splits shared types into their own installable package (e.g. a
`packages/shared-types` with its own `pyproject.toml`) when two or more
**separately deployable, separately versioned** services need to share a
type without importing each other's code wholesale. That problem doesn't
exist here: `graph.py` (running inside `langgraph dev`) and `webhook.py`
(running under `uvicorn`) are two processes, but they both come from the
same package install (`uv sync` against the one `uv.lock`) — a plain
`import crmToVoice.models` works identically for both, no packaging
boundary needed. `models/` is just an organizational subpackage, the same
role a `schemas/` folder plays in a typical single-service FastAPI project.

## Why some things stay in Portuguese

Two, and only two, categories of name are intentionally *not* English,
because they're not a documentation-language choice — they're external,
already-real identifiers that this repo doesn't control:

- **The live Airtable base itself**: base name ("CRM Imobiliário (Voz)"),
  workspace ("Porjeto"), table names (Leads, Imóveis, Visitas), and every
  field name inside them (Nome, Estado, Morada, ...). Renaming these in a
  doc without renaming the real base would just make the doc wrong.
- **Epic 01's already-shipped, CI-passing code** (`airtable/imoveis.py`,
  `airtable/visitas.py`, and their function/parameter names like
  `create_imovel`, `search_leads(nome)`) — these were written and tested
  against the field names above. Renaming them is a source-code refactor
  of finished work (touching every call site and every test), tracked as
  its own decision, not folded silently into a docs-translation pass.

Everything else — prose, Epic 02+ design vocabulary (`AgentState` fields,
node names, file names like `create.py`), and epic/backlog documents — is
English, including where it wasn't before.

## Built vs planned, at a glance

| Area | Status | Epic |
|---|---|---|
| `airtable/` (data access) | ✅ done | 01 |
| `models/` (Pydantic schemas) | 🔲 not started | 02 |
| `agents/tools/`, LLM config | 🔲 not started | 02 |
| `agents/middleware/` + routers + `read.py` | 🔲 not started | 03 |
| `agents/catalog/crmAgent/create.py` | 🔲 not started | 04 |
| `agents/catalog/crmAgent/update.py` | 🔲 not started | 05 |
| `agents/catalog/crmAgent/delete.py` | 🔲 not started | 06 |
| `webhook.py` | 🔲 not started | 07 |
