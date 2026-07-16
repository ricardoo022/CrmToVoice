# tools

Wraps the Epic 01 `airtable/` layer (`leads.py`, `imoveis.py`, `visitas.py`) as LangChain tools —
the graph's write/read boundary, used only at the *end* of a path (create/update/delete/query).
Doesn't talk to `pyairtable` directly.

**Status: done (US-AG-02).** One file per table, mirroring `airtable/`'s split
(`leads.py`, `imoveis.py`, `visitas.py`), each a thin `@tool`-decorated 1:1 passthrough to the
matching Epic 01 function — no validation, wizard logic, or find-or-create behavior lives here,
that stays in the path nodes (Epics 03-06). `__init__.py` re-exports every tool, so callers import
from `crmToVoice.agents.tools` without knowing which file a tool lives in. `search_leads`/
`search_imoveis` are included too, even though they're consumed by the future Context Middleware
(Epic 03) rather than a Create/Read/Update/Delete path node directly.
