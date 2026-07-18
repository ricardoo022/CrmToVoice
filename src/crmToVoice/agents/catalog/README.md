# catalog

Where LLM agents themselves get built — `create_agent(...)` calls (model, tools, prompt), one
subfolder per agent. Nothing here is a `StateGraph` node — a `catalog/` factory just returns a
runnable/compiled agent. In Tag 1 there's no `StateGraph` at all: `webhook.py` calls straight into
`interpret_speech/`'s factory and invokes it directly.

**Status: done (Tag 1, Epic 03 US-T1-01).**

| Folder | Purpose |
|---|---|
| `interpret_speech/` | The Tag 1 all-tools agent: `create_interpret_speech_agent(checkpointer=None)`, bound to **all 18** tools from `agents/tools/` (read + write), no `response_format` — it replies with free-form Portuguese text, not structured output. `checkpointer` stays a parameter (default `None`, agent is stateless) so it's testable in isolation and available if Tag 2 ever wants to pass one in. |

`interpret_speech/` splits into `prompt.py` (the system prompt implementing `docs/CRM.md`'s
field/classification rules plus the search-before-create / confirm-before-delete / ask-for-
missing-info behaviors from `docs/backlog/epics/epic-03-tag-1-single-agent.md`) and `agent.py`
(the factory itself), so the prompt — the part most likely to get iterated on against real
utterances — can be read/edited/tested without touching the agent-assembly code. Note: the agent
factory does *not* pass `system_prompt` to `create_agent()` — the caller (`webhook.py`, tests)
builds a fresh `SystemMessage(render_system_prompt())` per call instead, so the prompt's
`{{TODAY}}`/`{{WEEKDAY}}` date anchor is never stale on a long-lived cached agent.

`models/interpretation.py`'s `Interpretation` schema (the old structured-output contract) is
**not** used here — it was built for the original multi-node design and is reserved for Tag 2.
