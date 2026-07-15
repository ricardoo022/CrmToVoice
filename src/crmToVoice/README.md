# crmToVoice

| File / Folder | Purpose |
|---|---|
| `__init__.py` (empty) | Marks `crmToVoice` as a package. |
| `airtable/` | Epic 01, done. The Airtable data-access layer — see `airtable/README.md`. |
| `models/` | Epic 02, in progress. Every Pydantic model used by the agent — see `models/README.md`. |
| `agents/` | Epic 02+, not built yet. The LangGraph agent (middleware/tools/catalog) — see `agents/README.md`. |
| `graph.py` (empty stub) | Will define the compiled `StateGraph` (graph key `crmAgent` in `langgraph dev`). Not built yet. |
| `config.py` (not yet created) | Planned LLM settings (OpenRouter model, etc.), read from env. Doesn't exist as a file yet. |
| `webhook.py` (not yet created) | Planned FastAPI adapter exposing the graph to the iPhone Shortcut (`crmToVoice.webhook:app`). Doesn't exist as a file yet. |

See `docs/Agent.md` for the full design and `docs/superpowers/specs/2026-07-14-agent-runtime-design.md`
for the runtime decisions (LLM provider, hosting, checkpointer, payload format).
