# agents

The graph itself — state, routers, and nodes described in `docs/Agent.md` §9.

| Folder | Purpose |
|---|---|
| `middleware/` | Not built yet (Epic 03+). Deterministic Context Middleware (CRM lookups before the LLM runs) — see `middleware/README.md`. |
| `tools/` | Epic 02, done. Airtable read/write operations wrapped for the graph — see `tools/README.md`. |
| `catalog/` | Not built yet (Epic 04+). Per-intent path logic (Criar/Ler/Atualizar/Apagar), grouped by agent — see `catalog/README.md`. |
