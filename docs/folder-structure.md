# Folder structure

This is a **single-package repository**, not a multi-package monorepo: one
`pyproject.toml`, one `uv.lock`, one Python dependency graph. The Docker
image (`Dockerfile.webhook`) does `uv sync` and serves the webhook via
`uvicorn crmToVoice.webhook:app`.

Legend: ✅ built · 🔲 planned (Tag 2+) · 📝 Tag 1 in progress

```
CrmToVoice/
├── docs/                              — design docs, authoritative; read before writing code
│   ├── CRM.md                         — Airtable data model + voice-action catalog (Create/Read/Update/Delete)
│   ├── Agent.md                       — Agent design: Tag 1 single-agent approach, Tag 2 vision
│   ├── siri-shortcut-integration.md   — iPhone Shortcut side (dictation, webhook call, response parsing)
│   ├── folder-structure.md            — this file
│   ├── interpret-speech-eval-findings.md — Tag 1 eval results against the all-tools agent
│   └── backlog/epics/                 — one file per epic, checkboxed acceptance criteria
│       ├── epic-01-database.md        — ✅ done
│       ├── epic-02-agent-foundations.md — ✅ done
│       └── epic-03-tag-1-single-agent.md — 🏗️ in progress (Tag 1 MVP)
│
├── src/
│   └── crmToVoice/                    — the one installable package
│       ├── __init__.py
│       ├── config.py                  — ✅ Epic 02 — OpenRouter model/chat-client config, read from env
│       ├── webhook.py                 — 📝 FastAPI adapter; exposes `POST /webhook` matching the Shortcut's
│       │                                 `{session_id, text}` → `{session_id, reply_text, done}` contract;
│       │                                 creates the agent, invokes it, returns the response
│       ├── graph.py                   — 🔲 empty stub (Tag 2+ — adds StateGraph when multi-node needed)
│       │
│       ├── models/                    — ✅ Epic 02 — every Pydantic model, one subpackage
│       │   ├── __init__.py            —   re-exports the public models
│       │   ├── state.py               —   `AgentState` (available for Tag 2; not used directly in Tag 1)
│       │   ├── fields.py              —   `LeadFields` / `PropertyFields` / `VisitFields`
│       │   └── interpretation.py      —   structured-output schema (available for Tag 2)
│       │
│       ├── airtable/                  — ✅ Epic 01 — plain data-access layer, no LangChain/agent concerns
│       │   ├── client.py              —   cached `pyairtable` connection (`get_api()`, `get_table()`)
│       │   ├── leads.py               —   create/read/update/delete/search over Leads
│       │   ├── imoveis.py             —   create/read/update/delete/search over Imóveis (Properties)
│       │   └── visitas.py             —   create/read/update/delete/query over Visitas (Visits)
│       │
│       └── agents/                    — ✅ Epic 02 (tools), 📝 Tag 1 (agent), 🔲 Tag 2 (nodes)
│           ├── tools/                 — ✅ all 18 @tool-decorated functions (read + write)
│           ├── catalog/
│           │   └── interpret_speech/  — 📝 the single agent factory; Tag 1 binds ALL tools
│           └── nodes/                 — 🔲 not needed until Tag 2 adds StateGraph paths
│
├── tests/
│   ├── unit/                          — external services mocked/faked, fast, no credentials
│   │   └── airtable/                  — ✅ Epic 01 tests
│   └── integration/                   — hits real Airtable/OpenRouter; runs locally and in CI
│       ├── conftest.py                — auto-loads `.env` locally, never overrides real env vars (CI-safe)
│       └── airtable/                  — ✅ real Airtable base, cleans up every record it creates
│
├── db/                                — 🔲 holds the SQLite checkpointer file at runtime (local dev only);
│                                          not source, only appears once the agent has actually run
│
├── docker-compose.yml                 — single `webhook` service (port 8000)
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
exist here: everything runs inside the `webhook.py` process (Tag 1), or
within a single `langgraph dev` process (Tag 2) — there are never two
separately deployed services sharing a type. `models/` is just an
organizational subpackage, the same role a `schemas/` folder plays in a
typical single-service FastAPI project.

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
node names), and epic/backlog documents — is English.

## Built vs planned, at a glance

| Area | Status | Epic |
|---|---|---|
| `airtable/` (data access) | ✅ done | 01 |
| `models/` (Pydantic schemas) | ✅ done | 02 |
| `agents/tools/`, LLM config | ✅ done | 02 |
| Single all-tools agent | 📝 in progress | 03 (Tag 1) |
| `webhook.py` (FastAPI) | 📝 in progress | 03 (Tag 1) |
| Multi-node graph + wizard + confirm | 🔲 planned | Tag 2 |
