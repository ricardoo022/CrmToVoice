# crmToVoice

The `crmToVoice` package: the Airtable data-access layer, the LangGraph agent
(middleware/tools/catalog), and the webhook adapter that exposes it to the
iPhone Shortcut.

- `airtable/` — Epic 01, done: plain create/read/update/delete/search functions
  over the Airtable base, no LangChain/agent concerns.
- `agents/`, `webhook.py` — Epic 02/03, not built yet; will consume `airtable/`.

See `docs/Agent.md` for the full design and `docs/superpowers/specs/2026-07-14-agent-runtime-design.md`
for the runtime decisions (LLM provider, hosting, checkpointer, payload format).
