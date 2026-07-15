# middleware

The deterministic Context Middleware (`docs/Agent.md` §3, node name `resolve_context` in §9's
node table) — resolves any Lead/Imóvel named in the incoming text against Airtable *before* the
LLM reasoning runs. Runs on every turn, new session or continuing one; never decides intent, only
enriches state with real CRM data so the agent doesn't have to guess or hallucinate. Read-only —
must stay that way per the idempotency-before-`interrupt()` rule.

Uses the search functions from the Epic 01 data-access layer (`airtable/leads.py::search_leads`,
`airtable/imoveis.py::search_imoveis`) — the only place in the agent allowed to call them.

No files exist here yet (Epic 02+, not built) — the per-file breakdown isn't decided yet.
