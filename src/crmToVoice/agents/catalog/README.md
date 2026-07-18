# catalog

Where LLM agents themselves get built — `create_agent(...)` calls (model, tools, prompt,
`response_format`), one subfolder per agent. Nothing here is a `StateGraph` node: a `catalog/`
factory just returns a runnable/compiled agent. `nodes/` is what calls it, invokes it, and merges
its output into `AgentState` — the node-vs-agent split mirrors Epic 03's `US-GR-03` (build the
agent, here) vs. `US-GR-04` (the node that wraps it).

No files exist here yet (Epic 03+, not built).

| Folder | Purpose |
|---|---|
| `interpret_speech/` | Router 2's agent: `create_interpret_speech_agent(checkpointer=None)`, bound to the read-only `search_leads`/`search_imoveis` tools (`agents/tools/`), with `response_format=Interpretation` (`models/interpretation.py`). `checkpointer` is a parameter rather than hardcoded so it stays testable in isolation — real graph wiring (`US-GR-04`/`US-GR-06`) is expected to pass `checkpointer=True` to inherit the outer graph's. |

`interpret_speech/` splits into `prompt.py` (the system prompt implementing `CRM.md`'s
classification/extraction rules) and `agent.py` (the factory itself), so the prompt — the part
most likely to get iterated on against real utterances — can be read/edited/tested without
touching the agent-assembly code.
