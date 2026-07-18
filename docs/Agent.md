# Agent (LangChain) — Documentation

This document covers the design of the agent that connects the Siri
Shortcut to the CRM (see `CRM.md` for the data structure and actions).

---

## Tag 1 architecture (current — single all-tools agent)

### Flow

```
[Siri dictation] → POST /webhook {session_id, text}
    → create_agent (ALL tools bound: read + write)
    → {session_id, reply_text, done: True}
```

A single LangChain `create_agent` with all Airtable tools bound. No
StateGraph, no `interrupt()`, no wizard, no confirmation — the LLM
decides autonomously what action to take and executes it directly.

### Why this approach for Tag 1

Get a working end-to-end flow into the hands of a real estate agent as fast
as possible. A single agent that can create/read/update/delete CRM records
from dictation is useful on its own. The multi-node graph with
`interrupt()`-based wizard and confirmations (Tag 2) adds safety and
structure, but doesn't need to block first delivery.

### Agent composition

| Component | Details |
|---|---|
| Model | `get_chat_model()` — OpenRouter via `ChatOpenAI` (see `config.py`) |
| Tools | **All** `agents/tools/`: `create_lead`, `update_lead`, `delete_lead`, `search_leads`, `get_lead`, `find_lead`, `create_imovel`, `update_imovel`, `delete_imovel`, `search_imoveis`, `get_imovel`, `find_imovel`, `create_visita`, `update_visita`, `delete_visita`, `get_visita`, `list_visitas_by_date_range`, `list_visitas_by_lead` |
| Response format | None (free-form text reply) — the agent speaks back to the user directly |
| Checkpointer | `True` (inherits the webhook's checkpointer for session history) |
| System prompt | Modified version of `agents/catalog/interpret_speech/prompt.py`: removes the "never write" constraint, adds instructions for when to call write tools |

### Session model

- Each Shortcut execution ("Hey Siri...") is an **isolated thread** with a
  unique `session_id` — never inherits context from previous executions.
- Within one execution, the Shortcut may call the webhook multiple times
  (same `session_id`) if the agent asks a follow-up question.
- Session history (conversation turns) is persisted via the checkpointer
  indexed by `thread_id` = `session_id`.
- Long-term memory = **the CRM itself (Airtable)** — the agent looks up
  leads/properties directly when needed.

### Webhook contract

Same as the original design, unchanged:

```
Request:  POST /webhook  { "session_id": "...", "text": "..." }
Response: { "session_id": "...", "reply_text": "...", "done": true }
```

For Tag 1, `done` is always `true` — the agent replies in a single turn.
Multi-turn exchanges (where `done: false` triggers another dictation round)
are a Tag 2 addition.

### File layout

```
src/crmToVoice/
├── webhook.py              — FastAPI adapter, POST /webhook; creates and
│                              invokes the agent, returns response
├── agents/
│   ├── catalog/
│   │   └── interpret_speech/
│   │       ├── agent.py    — create_interpret_speech_agent() — now binds
│   │       │                  ALL tools (not just read-only)
│   │       ├── prompt.py   — system prompt (modified for write tools)
│   │       └── __init__.py
│   ├── tools/              — all 18 @tool functions (unchanged)
│   └── nodes/              — 🔲 not needed until Tag 2
├── graph.py                — 🔲 empty stub until Tag 2 adds StateGraph
├── models/                 — AgentState, fields, Interpretation
└── config.py               — OpenRouter model/client configuration
```

### Error handling

- **LLM call fails** (timeout/API error) → webhook returns HTTP 500, the
  Shortcut can speak a generic "error" message.
- **Agent tries to create a duplicate** → the LLM should search first
  before creating (enforced via prompt instruction); the underlying
  Airtable functions don't prevent duplicates — this is the LLM's
  responsibility in Tag 1.
- **Unrecognizable input** → the agent replies asking the person to repeat
  themselves (same fallback as before).

### What Tag 1 does NOT include

| Feature | Reason |
|---|---|
| `interrupt()` / pause-resume | Adds complexity (idempotency safety) that isn't needed for an MVP |
| Confirmation before delete | The LLM is trusted to only delete when asked — Tag 2 adds confirmation |
| Missing-field wizard | The LLM can ask follow-ups conversationally, but there's no structured wizard |
| StateGraph | Not needed when there's only one node — `create_agent` is already a compiled graph internally |
| `graph.py` | Stub — will be wired when Tag 2 introduces multiple nodes |

---

## Tag 2 (future — structured multi-node graph)

Reintroduces the original multi-node design: separate router agent
(read-only tools) + intent paths (write tools) + `interrupt()` for
confirmation and wizard. See `docs/backlog/epics/epic-XX-tag-2.md` when
that work begins.

The key constraint that drove the original design — idempotency before
`interrupt()` — becomes relevant only when Tag 2 adds `interrupt()`:
a node that re-runs on resume must not re-execute a write. The Tag 1
single-agent approach avoids this by having no `interrupt()` at all.

---

## Input

- The Shortcut uses the **iPhone's native dictation** (Siri already
  transcribes speech). The webhook receives **text**, not audio — no
  transcription node in the graph.

---

## 3. (Legacy) Original layered architecture

The original design (see git history before the Tag 1 simplification) had
a layered architecture with one router (`interpret_speech`, read-only tools)
plus four deterministic paths with `interrupt()`-based wizard and
confirmation. That design remains as a reference for Tag 2 and is preserved
in the `docs/backlog/epics/epic-03-graph-core-read-path.md` git history.
