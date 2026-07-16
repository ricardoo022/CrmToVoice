# crmToVoice

| File / Folder | Purpose |
|---|---|
| `__init__.py` (empty) | Marks `crmToVoice` as a package. |
| `airtable/` | Epic 01, done. The Airtable data-access layer — see `airtable/README.md`. |
| `models/` | Epic 02, done. Every Pydantic model used by the agent — see `models/README.md`. |
| `agents/` | Epic 02 (`tools/`) done, Epic 03+ (`nodes/`) not built yet. The LangGraph agent — see `agents/README.md`. |
| `graph.py` (empty stub) | Will define the compiled `StateGraph` (graph key `crmAgent` in `langgraph dev`). Not built yet. |
| `config.py` | Epic 02, done. `get_openrouter_model()` (reads `OPENROUTER_MODEL`, no model hardcoded) and `get_chat_model()` (`lru_cache`d `ChatOpenAI` client pointed at OpenRouter, keyed by `OPENROUTER_API_KEY`) — the reusable client future LLM nodes (`interpret_speech`, `read_format_response`) call instead of each reimplementing it. |
| `webhook.py` (not yet created) | Planned FastAPI adapter exposing the graph to the iPhone Shortcut (`crmToVoice.webhook:app`). Doesn't exist as a file yet. |

See `docs/Agent.md` for the full design, including §8 for the runtime decisions
(LLM provider, hosting, checkpointer, payload format).
