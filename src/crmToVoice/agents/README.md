# agents

| Folder | Purpose |
|---|---|
| `tools/` | Epic 02, done. All 18 Airtable read/write operations wrapped as LangChain tools — see `tools/README.md`. |
| `catalog/` | Tag 1, done. Where LLM agents themselves get constructed — `create_interpret_speech_agent()` (model + all 18 tools, no structured output), one subfolder per agent — see `catalog/README.md`. |
| `nodes/` | Tag 2, not built yet. Every StateGraph node function the future multi-node graph needs (router, four intent handlers, final response) — would call into `catalog/` to get an agent instance rather than constructing one inline — see `nodes/README.md`. |

In Tag 1, `webhook.py` (`src/crmToVoice/webhook.py`) calls `agents/catalog/interpret_speech`'s
factory directly — there's no `StateGraph`, so nothing under `agents/` decides graph structure yet.
`graph.py` (one level up) stays an empty stub until Tag 2 adds `add_node`/`add_edge`/`add_conditional_edges`
wiring, at which point `nodes/` becomes what it wires together.
