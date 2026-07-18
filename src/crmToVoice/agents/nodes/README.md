# nodes

Every StateGraph node function described in `docs/Agent.md` §9 — the single router
(`interpret_speech`/Router 2, which also absorbs context lookup — no separate deterministic step),
and the four intent handlers (create/read/update/delete), plus the shared final-response node.
No distinction in kind is made between these: the router and an intent handler are both just plain
functions. `graph.py` (`src/crmToVoice/graph.py`) is the only file that calls
`add_node`/`add_edge`/`add_conditional_edges` — nothing here decides graph structure.

Where a node is backed by an LLM agent (`interpret_speech`), the agent itself is built in
`agents/catalog/` (e.g. `create_interpret_speech_agent()`) — the node function here calls that
factory, invokes the agent, and merges its structured output into `AgentState`, rather than
constructing the agent inline.

No files exist here yet (Epic 03+, not built) — the per-file breakdown isn't decided yet.
