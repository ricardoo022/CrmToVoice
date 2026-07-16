# tools

Wraps the Epic 01 `airtable/` layer (`leads.py`, `imoveis.py`, `visitas.py`) as LangChain tools —
the graph's write/read boundary, used only at the *end* of a path (create/update/delete/query).
Doesn't talk to `pyairtable` directly.

**Status: done (US-AG-02).** One file per table, mirroring `airtable/`'s split, each a thin
`@tool`-decorated 1:1 passthrough to the matching Epic 01 function — no validation, wizard logic,
or find-or-create behavior lives here, that stays in the path nodes (Epics 03-06). `__init__.py`
re-exports every tool, so callers import from `crmToVoice.agents.tools` without knowing which file
a tool lives in.

| File | Tools |
|---|---|
| `leads.py` | `create_lead`, `update_lead`, `delete_lead`, `search_leads`, `get_lead` |
| `imoveis.py` | `create_imovel`, `update_imovel`, `delete_imovel`, `search_imoveis`, `get_imovel` |
| `visitas.py` | `create_visita`, `update_visita`, `delete_visita`, `get_visita`, `list_visitas_by_date_range`, `list_visitas_by_lead` |

`search_leads`/`search_imoveis` are included too, even though they're consumed by
`interpret_speech`/Router 2 (Epic 03) — as tools that agent binds and calls at its own
discretion to resolve name/address mentions — rather than by a Create/Read/Update/Delete
path node directly.

Since every function is `@tool`-decorated, callers invoke them as LangChain tools, not as plain
functions — e.g. `create_lead.invoke({"fields": {...}})`, not `create_lead({...})`.
