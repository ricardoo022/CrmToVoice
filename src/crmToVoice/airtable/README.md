# airtable

Epic 01, done. Plain data-access layer for the Airtable base "CRM Imobiliário (Voz)" (`appiFiRN7rzTMqyff`) — no LangChain/agent concerns.

| File | Purpose |
|---|---|
| `__init__.py` (empty) | Marks `airtable` as a package. |
| `client.py` | `get_api()` (cached `pyairtable.Api`), `get_table(name)`, `get_records_by_ids(table, ids)` — the single connection every other module goes through. |
| `leads.py` | `create_lead`, `update_lead`, `delete_lead`, `search_leads`, `get_lead` (expands linked Visitas) over the Leads table. |
| `imoveis.py` | `create_imovel`, `update_imovel`, `delete_imovel`, `search_imoveis`, `get_imovel` (expands linked Visitas) over the Imóveis (Properties) table. |
| `visitas.py` | `create_visita` (validates `fields["Lead"]` is set), `list_visitas_by_lead` (fetches all, filters client-side — no server-side formula for linked-record IDs) over the Visitas (Visits) table. |

Consumed by Epic 02's `agents/tools/` (writes/reads at the end of a path) and
`agents/middleware/` (search, before the LLM runs) — this package never talks
to LangChain/LangGraph itself.
