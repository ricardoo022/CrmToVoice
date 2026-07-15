# middleware

The deterministic Context Middleware (`docs/Agent.md` §3) — resolves any Lead/Imóvel
named in the incoming text against Airtable *before* the LLM reasoning runs. Runs on
every turn, new session or continuing one; never decides intent, only enriches state
with real CRM data so the agent doesn't have to guess or hallucinate.

Uses the search functions from the Epic 01 data-access layer
(`src/crmToVoice/airtable/leads.py::search_leads`,
`airtable/imoveis.py::search_imoveis`, already built) — this is the only place
in the agent allowed to call them.
