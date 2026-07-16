# Epic 03 — Graph Core + Read Path

**Status:** 🚧 Draft (defining acceptance criteria)

**Goal:** Build the minimal end-to-end graph that can answer CRM read queries.
This is the first vertical slice — proves the StateGraph, the router, and
LLM classification (including the LLM's own search tool-calling) all work
together before adding interrupt/resume complexity (Delete/Update/Create
paths).

**Out of scope for this epic:** the Create/Update/Delete paths, the webhook
adapter (Epic 04), any `interrupt()` calls (first used in Epic 05 — Delete).

**Depends on:**

- Epic 01 (`src/crmToVoice/airtable/`) — done
- Epic 02 (`src/crmToVoice/models/`, `agents/tools/`, `config.py`) — done

---



## US-GR-01 — Session Router (Router 1)

**Status:** ⛔ Reverted — deferred until Epic 05

Built once (`session_router(state) -> Literal["new", "resume_path"]`, a
conditional edge reading `state.pending_question`), then removed after review.
Reasoning, kept here so it isn't rediscovered the hard way:

1. **No current fork depends on it.** Both outputs route to the same next
   node (`interpret_speech`) — today and in the general design
   (`interpret_speech` always runs, new or continuing). A conditional edge
   whose branches converge is a no-op `add_edge` wearing a router's clothes.
2. **"Fetch context for this session" isn't code we write.** LangGraph's
   checkpointer already loads whatever state exists for a `thread_id` before
   any node runs — confirmed empirically (`graph.get_state(config)` exposes
   pending interrupts via `.tasks[i].interrupts` with zero custom state
   needed). There's no "go look it up" step to build.
3. **The one real reason for a router — deciding new vs. resuming — depends
   on which HIL resume mechanism Epic 05 picks, which isn't decided yet:**
   - `Command(resume=...)` (LangGraph's native pattern): resumes execution
     directly inside the interrupted node; `session_router` never re-runs on
     a continuing turn — the new/resume decision, if needed at all, would
     happen in the **webhook** (peeking at `graph.get_state(config)` before
     choosing `Command(resume=...)` vs. a plain `invoke()`), not as a node
     inside the graph.
   - Plain `invoke()` with a fresh dict (what the current `docs/Agent.md`
     diagram draws — the `-.next call, same session.-> R1` dashed line):
     restarts the whole graph from `START`, confirmed empirically
     (a pre-interrupt node re-ran from scratch on the second `invoke()`).
     `pending_question` as an explicit `AgentState` field only earns its
     keep under *this* mechanism.

   Building `session_router` (and the `pending_question`/
   `awaiting_delete_confirmation` fields it depends on) committed to the
   second option without that decision ever being made deliberately — it
   was implied by a diagram, not verified against real `interrupt()`
   behavior until this review.

**Revisit this story in Epic 05** (first real `interrupt()` user, Delete),
once the resume mechanism is actually chosen: decide `Command(resume=...)`
vs. restart-from-`START` first, then build only the routing code that
mechanism actually requires — which may not be a `session_router` node at
all.

---



## US-GR-04 — Interpret Speech + Action Router (Router 2)

One LLM agent node, bound to the read-only `search_leads`/`search_imoveis`
tools. Given `current_input` (+ session history), it decides for itself
whether a name/address mention is worth looking up, calls the search
tool(s) if so, and returns `intent`, `target_entity`, `extracted_fields`
(and whatever it resolved into `crm_context`) as one structured output;
the same node's conditional edge reads `intent` and dispatches to one of
the 4 subgraphs. There is no separate deterministic context-resolution
step before this node — see "Open notes for review" below.

*(To be drafted)*

---



## US-GR-05 — Read Path

*(To be drafted)*

---



## US-GR-06 — Graph Wiring + Checkpointer

*(To be drafted)*

---



## Open notes for review

- Placeholder user stories (US-GR-04 through US-GR-06) will be drafted
incrementally as we complete each section. `US-GR-02` was deleted — the
"Interpret Speech Node" it would have covered was merged into `US-GR-04`
once the graph order changed so the LLM call and Router 2's dispatch
became one unit of work instead of two separate nodes/stories.
- `US-GR-03` ("Context Middleware") was deleted, not just drafted
differently: there is no deterministic pre-LLM node that resolves
name/address mentions. `interpret_speech` (`US-GR-04`) is itself an agent
with `search_leads`/`search_imoveis` bound as tools — it decides on its
own, per turn, whether to call them. This is a deliberate architecture
decision (see `Agent.md` §3/§6): those two tools are read-only, so
letting the agent decide *when* to search carries none of the
write-duplication risk that giving it discretion over create/update/
delete would.
- The `"resume_path"` target returned by session_router is a forward reference
— it won't exist until Epic 05 (Delete) adds the first path with
`interrupt()`.

