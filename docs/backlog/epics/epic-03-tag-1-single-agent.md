# Epic 03 — Tag 1: Single All-Tools Agent MVP

**Status:** 🏗️ In progress

**Goal:** Finish the `interpret_speech` agent itself — bind all 18 Airtable
tools (read + write) and update the system prompt so it can safely create,
read, update, and delete CRM records directly. No StateGraph, no
`interrupt()`, no wizard. The webhook/Siri wiring that exposes this agent to
the outside world is a separate, simpler epic (see
`docs/backlog/epics/epic-04-siri-integration.md`).

**Out of scope for this epic:** the multi-node graph with separate router
and paths, `interrupt()`-based confirmation and wizard, structured
`Interpretation` output, `AgentState`-based graph state. Everything above
is deferred to Tag 2.

**Depends on:**

- Epic 01 (`src/crmToVoice/airtable/`) — done
- Epic 02 (`src/crmToVoice/models/`, `agents/tools/`, `config.py`) — done

---

## US-T1-01 — A single agent that can create, read, update, and delete

As a real estate agent
I want to say one thing to Siri and have the CRM agent handle it end to end
So that I don't need separate tools or steps for creating a lead, checking
on one, correcting something, or removing one — one agent does all of it

**What we want:**

- One `create_agent`, bound to all 18 CRM tools (Leads, Imóveis, Visitas —
  read and write). No separate read-only router, no separate write path.
- From a single dictated sentence, the agent can:
  - **Create** a new Lead, Imóvel, or Visita
  - **Read** — answer questions about existing Leads/Imóveis/Visitas
  - **Update** an existing record (e.g. a Lead's status, a phone number, a
    budget)
  - **Delete** a Lead, Imóvel, or Visita
- Before creating something, the agent checks whether it already exists
  (searches by name/address) instead of blindly creating a duplicate.
- Before deleting something, the agent asks the person to confirm out loud
  and only deletes if they say yes.
- If required information is missing to complete an action, the agent asks
  for it conversationally instead of guessing or failing silently.
- The agent always replies in Portuguese, in plain spoken-style text — no
  structured/JSON output, since a Shortcut will just read the reply aloud.

---

## US-T1-02 — Eval suite for the all-tools agent

As a developer
I want an automated eval suite that exercises the all-tools agent against
real OpenRouter and Airtable
So that I can measure quality and catch regressions before each deployment

**Acceptance Criteria:**

- [ ] `scripts/eval_all_tools_agent.py` (replaces the old
      `eval_interpret_speech.py`) uses LangSmith deterministic evaluators
- [ ] Covers at minimum: one create example, one read example, one update
      example, one delete example
- [ ] Each example verifies:
      - Tool usage (correct tool(s) were called)
      - No duplicate create (searches before creating)
      - Delete confirmation asked before delete tool called
      - Correct Airtable record state after the agent runs
- [ ] Fixture records created before run, deleted after (same pattern as
      existing eval script)
- [ ] `make eval-all-tools` target in Makefile

---

## Open notes for review

- The old US-GR-03 (read-only `interpret_speech` agent), US-GR-04 (router
  node + conditional edge), US-GR-05 (read path), and US-GR-06 (graph
  wiring) are **cancelled** — they described the original multi-node
  architecture that Tag 1 replaces. Their content is preserved in git
  history for reference when Tag 2 begins.
- `AgentState`, `Interpretation`, and the `models/` package were built for
  the multi-node architecture. Tag 1 doesn't use them (the agent responds
  with free text, not structured output). They remain in the codebase and
  are available for Tag 2.
- `graph.py` is not used in Tag 1 — the webhook invokes the agent directly.
  `graph.py` stays as an empty stub until Tag 2 adds the StateGraph.
- The webhook and Siri Shortcut work (previously US-T1-03/US-T1-04 here)
  moved to `docs/backlog/epics/epic-04-siri-integration.md` — once this
  epic's agent is done, wiring it up is a separate, simpler piece of work.
