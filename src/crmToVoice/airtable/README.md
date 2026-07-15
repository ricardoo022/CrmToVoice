# airtable

Epic 01 — the data-access layer for the Airtable base "CRM Imobiliário (Voz)"
(`appiFiRN7rzTMqyff`). Plain functions, no LangChain/agent concerns: `client.py`
holds the single cached connection (`AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID`), and
`leads.py`/`imoveis.py`/`visitas.py` each expose create/read/update/delete
(+ search/query) for their table, per `docs/CRM.md` §1 field lists.

Consumed by Epic 02's `agents/tools/` (writes/reads at the end of a path) and
`agents/middleware/` (search, before the LLM runs) — this package never talks
to LangChain/LangGraph itself.
