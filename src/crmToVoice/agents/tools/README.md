# tools

Airtable read/write operations, used only at the end of each path (create/update/delete
or query). The agent never uses these to *search* — that's the middleware's job — only
to persist or read once a path has decided what to do.

Wraps the Epic 01 data-access layer (`src/crmToVoice/airtable/` — `leads.py`,
`imoveis.py`, `visitas.py`, already built) as LangChain tools; doesn't talk to
`pyairtable` directly.
