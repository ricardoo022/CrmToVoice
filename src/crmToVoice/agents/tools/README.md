# tools

Wraps the Epic 01 `airtable/` layer (`leads.py`, `imoveis.py`, `visitas.py`) as LangChain tools —
the graph's write/read boundary, used only at the *end* of a path (create/update/delete/query),
never to search (that's `middleware/`'s job). Doesn't talk to `pyairtable` directly.

No files exist here yet (Epic 02+, not built) — the per-file breakdown isn't decided yet.
