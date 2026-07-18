# crmToVoice

| File / Folder | Purpose |
|---|---|
| `__init__.py` (empty) | Marks `crmToVoice` as a package. |
| `airtable/` | Epic 01, done. The Airtable data-access layer — see `airtable/README.md`. |
| `models/` | Epic 02, done. Every Pydantic model — built for Tag 2, not used by the Tag 1 agent (which replies with free text, not structured output) — see `models/README.md`. |
| `agents/` | Epic 02 (`tools/`) done, Tag 1 (`catalog/`) done, Tag 2 (`nodes/`) not built yet — see `agents/README.md`. |
| `config.py` | Epic 02, done. `get_openrouter_model()` (reads `OPENROUTER_MODEL`, no model hardcoded) and `get_chat_model()` (`lru_cache`d `ChatOpenAI` client pointed at OpenRouter, keyed by `OPENROUTER_API_KEY`) — the reusable client every LLM caller (`agents/catalog/interpret_speech`) uses instead of each reimplementing it. |
| `webhook.py` | Tag 1, done. FastAPI adapter (`POST /webhook`) exposing the all-tools agent to the iPhone Shortcut — see `docs/Agent.md` (Tag 1 section). |
| `graph.py` (empty stub) | Tag 2. Will define the compiled `StateGraph` once the multi-node design is built. Not built yet. |

See `docs/Agent.md` for the full design — the Tag 1 section covers the
current single-agent + webhook flow; the Tag 2 section covers the future
multi-node graph.
