# nodes

**Tag 2 only — not needed by, or used in, Tag 1.** In Tag 1, `webhook.py` calls
`agents/catalog/interpret_speech`'s factory directly; there's no `StateGraph` and no router/path
split. This folder stays empty until Tag 2 builds the multi-node graph described in `docs/Agent.md`
(Tag 2 section): a router node (read-only tools, structured `Interpretation` output) plus four
intent-handler nodes (create/update/delete/read) with `interrupt()`-based wizard/confirmation, and
a shared final-response node. `graph.py` (`src/crmToVoice/graph.py`) would be the only file that
calls `add_node`/`add_edge`/`add_conditional_edges` — nothing here would decide graph structure.

Where a Tag 2 node is backed by an LLM agent (e.g. a router), the agent itself would still be built
in `agents/catalog/` — the node function here would call that factory, invoke the agent, and merge
its structured output into `AgentState`, rather than constructing the agent inline.

No files exist here yet — the per-file breakdown isn't decided (Tag 2, not started).
