# db

| File | Purpose |
|---|---|
| `checkpoints.db` (not committed, created at runtime) | SQLite file backing the LangGraph checkpointer (`AsyncSqliteSaver`, local dev only). See `docs/superpowers/specs/2026-07-14-agent-runtime-design.md` §3. |

No source files live here — this directory only exists to hold that runtime file.
