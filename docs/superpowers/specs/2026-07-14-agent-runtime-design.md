# Agent Runtime Design — resolving Agent.md §8

Date: 2026-07-14
Status: approved (design phase — no implementation yet)

## Context

`docs/Agent.md` describes the LangGraph agent (session model, two-router
four-path graph, `interrupt()`-based pause/resume). Section 8 of that document
left four implementation decisions open:

1. Model/LLM to use for the "Interpretar Fala" node
2. Where and how the graph runs (webhook hosting)
3. Checkpointer backend
4. Exact payload format between the Shortcut and the webhook

This spec resolves all four for the current phase of the project, which is
**local development only** — the goal right now is to run the agent on the
developer's own machine and interact with it from an iPhone on the same
Wi-Fi network, not to deploy it anywhere public.

## Decisions

### 1. LLM provider — OpenRouter

The "Interpretar Fala" node (single LLM call: intent + entity + field
extraction from Portuguese dictated text, per `Agent.md` §9) calls the model
through **OpenRouter** rather than a single provider's SDK directly.

- No specific underlying model is pinned in this spec. The model is a
  **config value** (e.g. an env var / config field holding an OpenRouter
  model slug), swappable without touching code.
- Rationale: keeps the door open to compare/change models (cost, quality,
  Portuguese support) without an SDK migration later.

### 2. Hosting — local dev server, LAN-only

No production deployment exists or is planned yet. The graph runs as a
**local dev server** on the developer's machine.

- Use **LangGraph's own local dev server** (`langgraph dev`) rather than a
  hand-rolled FastAPI wrapper. It already provides:
  - a REST endpoint to invoke the graph
  - `interrupt()` / resume handling
  - a pluggable checkpointer
  - the same abstraction that LangGraph Platform uses, so a future move to
    real hosting (if ever desired) is a config change, not a rewrite.
- The iPhone Shortcut reaches the dev server directly over the **same Wi-Fi
  network**: `http://<local-ip>:<port>/webhook`. No tunnel (ngrok/Cloudflare
  Tunnel) is used at this stage — both devices must be on the same network
  for the Shortcut to work.
- **Webhook adapter**: `langgraph dev` exposes LangGraph's own API shape
  (threads/runs), not the minimal `{session_id, text}` /
  `{session_id, reply_text, done}` contract in §4. A thin adapter
  (`src/crmToVoice/webhook.py`, a small FastAPI app) sits in front of it:
  it exposes `POST /webhook` matching §4 exactly, and internally calls the
  LangGraph client/SDK to run/resume the graph. The Shortcut only ever
  talks to this adapter, never to `langgraph dev`'s native API directly.
- Explicitly out of scope for this spec: public hosting, TLS, auth, uptime.
  These are deferred until/unless the project moves past local dev.

### 3. Checkpointer — SQLite (`AsyncSqliteSaver`), wired through `langgraph.json`

The LangGraph checkpointer uses **SQLite**, via `langgraph-checkpoint-sqlite`'s
`AsyncSqliteSaver`, pointed at a local file (e.g. `checkpoints.db`).

- **Scope**: short-term, per-thread memory only. It carries `AgentState`
  across turns *within* a single Shortcut execution (`thread_id =
  session_id`), so an `interrupt()`/resume (a wizard question, a
  confirmation, an ambiguous-name clarification) picks up exactly where it
  paused. This is required for the wizard to function at all, independent
  of which backend is chosen.
- **Why SQLite over `InMemorySaver`** (aka `MemorySaver`): `langgraph dev`
  hot-reloads on file changes during development, which restarts the
  process. SQLite lets an in-progress manual test survive that restart
  instead of losing wizard state every time a file is saved.
- **`langgraph dev` ignores `compile(checkpointer=...)` — this is the part
  that matters for how it gets wired up.** `langgraph dev` always runs its
  own in-memory runtime for the graph and, by design, discards any
  checkpointer passed at `.compile()` time — confirmed by a LangGraph
  maintainer ("`langgraph dev` is strictly for development and so it is by
  design that langgraph api will use an in-memory checkpointer",
  [langchain-ai/langgraph#5790](https://github.com/langchain-ai/langgraph/issues/5790)).
  Since this project's hosting decision (§2) is `langgraph dev`, the
  checkpointer must instead be declared through **`langgraph.json`**'s
  `checkpointer` field, which points to an async-context-manager factory
  function that yields the saver — not through a line in `graph.py`:

  `src/crmToVoice/checkpointer.py`:
  ```python
  import contextlib
  from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

  @contextlib.asynccontextmanager
  async def generate_checkpointer():
      async with AsyncSqliteSaver.from_conn_string("./checkpoints.db") as saver:
          await saver.setup()
          yield saver
  ```

  `langgraph.json`:
  ```json
  {
    "dependencies": ["."],
    "graphs": { "agent": "./src/crmToVoice/graph.py:graph" },
    "checkpointer": { "path": "./src/crmToVoice/checkpointer.py:generate_checkpointer" }
  }
  ```

  If the graph is ever invoked directly in Python instead of through
  `langgraph dev` (e.g. a script or a test), `compile(checkpointer=...)`
  with the same `AsyncSqliteSaver` works as normal — the `langgraph.json`
  path above only exists to work around `langgraph dev`'s override.
- **This is an alpha feature** (per LangChain's own docs on custom
  checkpointers) and may change in a minor `langgraph-cli` version bump.
  Confirm the installed `langgraph-cli` version still honors the
  `checkpointer` key in `langgraph.json` before relying on it; if it
  silently doesn't, `langgraph dev` falls back to in-memory with no error,
  which would look like working state persistence during a single
  process's lifetime but lose everything on the next hot-reload.
- Per `Agent.md` §2, this remains short-term memory only — it does **not**
  enable resuming a session across separate Shortcut executions. A new
  "Ei Siri" always starts a fresh `session_id`/thread; the rule that
  abandoned sessions are discarded, not resumed, is unchanged.
- **No schema design needed.** `AsyncSqliteSaver.setup()` creates and
  manages its own internal tables (`checkpoints`, `checkpoint_writes`,
  `checkpoint_blobs`) automatically. This SQLite file is entirely separate
  from the Airtable CRM — no new Airtable tables, and no hand-designed
  SQLite tables either.
- **Long-term/cross-session memory** (LangGraph's `Store`, shared across
  threads) is explicitly out of scope for this decision — parked for a
  future spec.

### 4. Shortcut ↔ webhook payload format — minimal JSON

**Request** (Shortcut → webhook):
```json
{
  "session_id": "string",
  "text": "string"
}
```

**Response** (webhook → Shortcut):
```json
{
  "session_id": "string",
  "reply_text": "string",
  "done": true
}
```

- `session_id` is generated by the Shortcut at the start of an execution and
  sent unchanged on every call within that execution (per `Agent.md` §2).
- `reply_text` is what the Shortcut hands to Siri to speak aloud.
- `done: false` means the graph is paused on an `interrupt()` (a wizard
  question, a confirmation, an ambiguous-name clarification). The Shortcut
  speaks `reply_text`, re-opens dictation for the next thing the person
  says, and POSTs again to the same webhook with the **same** `session_id`
  and the new dictated text.
- `done: true` means the cycle is finished (action completed, or the
  session ended in an error/cancellation) — the Shortcut speaks `reply_text`
  and stops.

## Non-goals (for this spec)

- Picking a specific OpenRouter model.
- Any production/public hosting decision.
- Authentication or rate-limiting on the webhook (irrelevant on a LAN-only
  dev server).
- Tunnel-based remote access (ngrok/Tailscale/etc.) — noted as a possible
  future need but not designed here.

## Open items now considered resolved

All four items from `docs/Agent.md` §8 are resolved by this spec for the
current project phase. `docs/Agent.md` §8 has been updated to point at this
spec.

## Epic sequencing for implementation (Epics 02–07)

With Epic 01 (Airtable data-access layer) complete, the rest of `Agent.md`/
`CRM.md` is built as a sequence of further epics, each independently
testable via `langgraph dev` before starting the next one:

- **Epic 02 — Agent Foundations**: `models/` (every Pydantic model —
  `AgentState`, per-entity field models, the `interpret_speech`
  structured-output schema; see `docs/folder-structure.md`),
  `agents/tools/` (thin wrappers around Epic 01's `airtable/` functions),
  LLM config for OpenRouter (§1 above). No graph, no routers, no paths yet
  — just the shared plumbing every later epic imports.
- **Epic 03 — Minimal graph + Read path**: `session_router`,
  `interpret_speech`, `action_router`, `resolve_context` (middleware), and
  the **Read** path end to end. Chosen as the first full path because it
  has no `interrupt()` — proves the graph/routers/middleware plumbing
  works via `langgraph dev` before pause/resume complexity is introduced.
- **Epic 04 — Create path (wizard)**: `create_check_fields`,
  `create_ask` (the `interrupt()`), `create_write`. First real
  exercise of the checkpointer — a session actually pausing and resuming
  across turns. Idempotency rule from `Agent.md` §6 (no Airtable create
  before the wizard's last `interrupt()` resolves) applies here.
- **Epic 05 — Update path**: direct field corrections + the
  `Estado`/"why?" flow (creates a linked Visit/Note). Reuses the
  `interrupt()` mechanism proven in Epic 04.
- **Epic 06 — Delete path**: confirmation-gated delete — smallest of
  the four paths, but "no explicit confirmation = no delete" must hold.
- **Epic 07 — Webhook (Siri integration)**: the FastAPI adapter in front
  of `langgraph dev` (§2, §4 above) that exposes the Shortcut's
  `{session_id, text}` → `{session_id, reply_text, done}` contract. The
  only epic that touches the actual iPhone/Shortcut side.

Epics 02–06 together deliver "the whole agent, fully functional via
`langgraph dev`" without needing the iPhone/Shortcut at all. Epic 07 is
what connects that to Siri.
