# agents

The graph itself — state, routers, and nodes described in `docs/Agent.md` §9 — split into:

- `middleware/` — deterministic Context Middleware (CRM lookups before the LLM runs)
- `tools/` — Airtable read/write operations
- `catalog/` — per-intent path logic (Criar/Ler/Atualizar/Apagar), grouped by agent
