# tools

Wraps the Epic 01 `airtable/` layer (`leads.py`, `imoveis.py`, `visitas.py`) as LangChain tools.
In Tag 1, the `interpret_speech` agent (`agents/catalog/`) is bound to **all 18** of these —
there's no read/write split by path, since there's no path/router at all, just one agent that
decides for itself which tool to call. Doesn't talk to `pyairtable` directly.

**Status: done (Epic 02 US-AG-02).** One file per table, mirroring `airtable/`'s split, each a
thin `@tool`-decorated 1:1 passthrough to the matching Epic 01 function, plus a composite
`find_*` tool per entity (search by name/address and return the full record, visits expanded, in
one call) — no validation, wizard logic beyond that lives here, that stays in the prompt/agent.
`__init__.py` re-exports every tool, so callers import from `crmToVoice.agents.tools` without
knowing which file a tool lives in.

| File | Tools |
|---|---|
| `leads.py` | `create_lead`, `update_lead`, `delete_lead`, `search_leads`, `get_lead`, `find_lead` |
| `imoveis.py` | `create_imovel`, `update_imovel`, `delete_imovel`, `search_imoveis`, `get_imovel`, `find_imovel` |
| `visitas.py` | `create_visita`, `update_visita`, `delete_visita`, `get_visita`, `list_visitas_by_date_range`, `list_visitas_by_lead` |

`search_leads`/`search_imoveis` vs. `find_lead`/`find_imovel`: the agent's prompt (`agents/catalog/interpret_speech/prompt.py`)
directs it to use `search_*` specifically for the pre-create duplicate check (list of matches, no
expansion) and `find_*` when it needs the full record to act on (status, history, update, delete).

Since every function is `@tool`-decorated, callers invoke them as LangChain tools, not as plain
functions — e.g. `create_lead.invoke({"fields": {...}})`, not `create_lead({...})`.
