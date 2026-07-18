# agents

The graph itself — state, the router, and nodes described in `docs/Agent.md` §9.

| Folder | Purpose |
|---|---|
| `tools/` | Epic 02, done. Airtable read/write operations wrapped for the graph — see `tools/README.md`. |
| `catalog/` | Not built yet (Epic 03+). Where LLM agents themselves get constructed — e.g. `create_interpret_speech_agent()` (model + tools + prompt + structured output), one subfolder per agent — see `catalog/README.md`. |
| `nodes/` | Not built yet (Epic 03+). Every StateGraph node function (the single router, which also absorbs context lookup, the four intent handlers, the final response node) — calls into `catalog/` to get an agent instance rather than constructing one inline — see `nodes/README.md`. |

`graph.py` (one level up, `src/crmToVoice/graph.py`) is the only file that calls
`add_node`/`add_edge`/`add_conditional_edges` — nothing under `agents/` decides graph structure,
these are just the plain functions it wires together.
