# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

The design is complete and the project is scaffolded (dependencies, folder architecture, Docker, CI). **Epic 01 (Base de Dados) is implemented** — `src/crmToVoice/airtable/` (`client.py`, `leads.py`, `imoveis.py`, `visitas.py`), with unit tests in `tests/unit/airtable/` and integration tests (real Airtable) in `tests/integration/airtable/`; see `docs/backlog/epics/epic-01-database.md`. Epic 02 (Agente) and Epic 03 (Webhook) are **not built yet** — the rest of `src/crmToVoice/` (`agents/`, `webhook.py`) is still a tree of empty directories, each with a `README.md` describing what belongs there. The design docs under `docs/` are authoritative and should be read before writing any code:

- `docs/CRM.md` — Airtable data model (Leads, Imóveis, Visitas tables, field lists) and the full catalog of voice-driven CRM actions (Criar/Ler/Atualizar/Apagar), including the field-classification rules (which fields are auto-filled vs. asked-if-missing) and the guided-wizard question mechanics.
- `docs/Agent.md` — the LangGraph agent design: session/memory model, the middleware/agent layering, the shared `AgentState`, the two-router four-path graph (Criar/Ler/Atualizar/Apagar), the `interrupt()`-based pause/resume mechanism, error/fallback handling, a node-to-file mapping (§9), and a Mermaid diagram of the full graph.
- `docs/superpowers/specs/2026-07-14-agent-runtime-design.md` — runtime decisions: LLM via OpenRouter (model left as a swappable config value), local-only hosting via `langgraph dev` + a thin FastAPI webhook adapter in front of it (no production deploy yet), SQLite checkpointer, and the exact Shortcut↔webhook JSON payload (`{session_id, text}` → `{session_id, reply_text, done}`).
- `docs/siri-shortcut-integration.md` — factual reference for the iPhone Shortcut side (voice trigger, dictation, the `Get Contents of URL`/JSON webhook call, response parsing, the multi-turn loop pattern), with items still needing hands-on verification called out explicitly (notably: whether plain `http://` to a LAN IP actually works from the Shortcuts app).

## Commands

Package manager is **uv**; all commands are also exposed as `make` targets (`make help` lists them, in Portuguese).

```
make setup           # uv sync — creates .venv, installs everything
make dev             # uv run langgraph dev (won't start until src/crmToVoice/graph.py exists)
make lint            # uv run ruff check .
make format          # uv run ruff format .
make typecheck       # uv run pyright
make test-unit       # uv run pytest tests/unit
make test-integration # uv run pytest tests/integration — hits real Airtable/OpenRouter, needs credentials
make test            # both of the above
make check           # lint + typecheck + test
```

Run a single test once tests exist: `uv run pytest tests/unit/path/to/test_file.py::test_name -v`.

Local multi-service run: `docker compose up` builds `Dockerfile.langgraph` (the `graph` service, port 2024) and `Dockerfile.webhook` (the `webhook` service, port 8000, talks to `graph` via `LANGGRAPH_API_URL=http://graph:2024`). Requires a populated `.env` (see `.env.example`); neither service will run until `src/crmToVoice/graph.py` and `webhook.py` exist.

## Git workflow

`main` is branch-protected on GitHub: `quality`, `integration`, and `docker-build` CI checks must pass before anything lands (`enforce_admins: true`, so this applies even to the repo owner). **Direct pushes to `main` are rejected** — use a feature branch + PR, even for small changes.

## Architecture

- **Package layout** (`src/crmToVoice/`): `graph.py` (StateGraph wiring), `state.py` (`AgentState`), `config.py` (settings), `webhook.py` (the FastAPI adapter), and `agents/` split into `middleware/` (the deterministic Context Middleware), `tools/` (Airtable reads/writes), and `catalog/crmAgent/` (the four intent paths — `criar.py`, `ler.py`, `atualizar.py`, `apagar.py`). `tests/unit/` and `tests/integration/` mirror this layout.
- **CRM backend**: Airtable base "CRM Imobiliário (Voz)" (base ID `appiFiRN7rzTMqyff`, workspace "Porjeto"), with three linked tables: Leads, Imóveis, Visitas.
- **Session model**: each Shortcut execution ("Ei Siri...") is an isolated thread/session (`session_id`). Short-term memory within a session is handled by the LangGraph checkpointer, keyed by `thread_id = session_id`. There is no memory across separate sessions — the Airtable CRM itself is the long-term memory; the agent looks up leads/properties by name instead of recalling past conversations. Interrupted sessions are discarded, not resumed — nothing is written to Airtable until an action is complete/confirmed.
- **Layering**: a deterministic **Context Middleware** resolves any Lead/Imóvel named in the incoming text against Airtable *before* the LLM reasoning runs, so the agent never queries Airtable to search — it only writes (create/update/delete) or reads (query) at the end of a path.
- **Graph shape**: two routers, four paths.
  - Router 1 (deterministic): is this session mid-wizard/mid-confirmation (a `pergunta_pendente` exists)? If so, skip re-classification and resume the active path.
  - Router 2 (LLM-classified on a fresh turn): routes to one of **Criar / Ler / Atualizar / Apagar**.
  - **Criar** is the only path with the missing-field wizard (asks only for fields the person didn't already mention, grouped by topic, accepts "não sei"/"salta").
  - **Atualizar** never asks for extra fields — except changing a Lead's `Estado`, which triggers a "porquê?" follow-up and creates a linked Visita (Nota) recording the reason, rather than a bare field update.
  - **Apagar** always requires explicit voice confirmation before deleting; no confirmation = no delete.
  - **Ler** never writes; if the referenced Lead/Imóvel isn't found, it says so rather than guessing.

## Product summary

Field real-estate agents don't log visits/leads in the CRM because typing is friction. The fix: the agent speaks to Siri ("Ei Siri, regista visita..."), an iPhone Shortcut sends the already-dictated text to a webhook, and a LangGraph agent turns that into structured Airtable CRM writes (or, for questions, reads the CRM and returns a spoken answer). The interaction is bidirectional and can be multi-turn (a guided wizard asks only for missing fields, grouped by topic) within a single Shortcut execution.
