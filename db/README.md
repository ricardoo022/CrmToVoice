# db

**Not used by Tag 1.** The current `interpret_speech` agent is stateless (no checkpointer —
`docs/Agent.md`, Tag 1 section); conversation continuity is an in-memory, per-`session_id` dict
inside `crmToVoice/webhook.py`, not a SQLite file. This directory is reserved for Tag 2, which is
expected to add a LangGraph `SqliteSaver`/`AsyncSqliteSaver` checkpointer for local dev.

| File | Purpose |
|---|---|
| `checkpoints.db` (not committed, not created yet) | Will hold the Tag 2 checkpointer's SQLite file once that's built. |

No source files live here — this directory only exists to hold that future runtime file.
