# agents

The graph itself — state, routers, and nodes described in `docs/Agent.md` §9. Not built yet (Epic 02+).

| Folder | Purpose |
|---|---|
| `middleware/` | Deterministic Context Middleware (CRM lookups before the LLM runs) — see `middleware/README.md`. |
| `tools/` | Airtable read/write operations wrapped for the graph — see `tools/README.md`. |
| `catalog/` | Per-intent path logic (Criar/Ler/Atualizar/Apagar), grouped by agent — see `catalog/README.md`. |
