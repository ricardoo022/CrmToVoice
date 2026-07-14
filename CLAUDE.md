# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository is currently **design-only** — there is no implementation code yet (no package manifest, no source directories, no tests). The files under `docs/` are the authoritative design specs and should be read before writing any code:

- `docs/CRM.md` — Airtable data model (Leads, Imóveis, Visitas tables, field lists) and the full catalog of voice-driven CRM actions (Criar/Ler/Atualizar/Apagar), including the field-classification rules (which fields are auto-filled vs. asked-if-missing) and the guided-wizard question mechanics.
- `docs/Agent.md` — the LangGraph agent design: session/memory model, the middleware/agent layering, the shared `AgentState`, the two-router four-path graph (Criar/Ler/Atualizar/Apagar), the `interrupt()`-based pause/resume mechanism, error/fallback handling, and a Mermaid diagram of the full graph. Section 8 covers runtime decisions (LLM provider, hosting, checkpointer backend, Shortcut↔webhook payload format) — resolved for the current local-dev-only phase in `docs/superpowers/specs/2026-07-14-agent-runtime-design.md`.
- `docs/siri-shortcut-integration.md` — factual reference for the iPhone Shortcut side (voice trigger, dictation, the `Get Contents of URL`/JSON webhook call, response parsing, the multi-turn loop pattern) with items still needing hands-on verification called out explicitly.

There are no build, lint, or test commands yet because there is no code to build, lint, or test.

## Product summary

Field real-estate agents don't log visits/leads in the CRM because typing is friction. The fix: the agent speaks to Siri ("Ei Siri, regista visita..."), an iPhone Shortcut sends the already-dictated text to a webhook, and a LangGraph agent turns that into structured Airtable CRM writes (or, for questions, reads the CRM and returns a spoken answer). The interaction is bidirectional and can be multi-turn (a guided wizard asks only for missing fields, grouped by topic) within a single Shortcut execution.

## Architecture (read `docs/Agent.md` for full detail)

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
