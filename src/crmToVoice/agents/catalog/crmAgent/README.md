# crmAgent

The four intent paths (`docs/Agent.md` §5). None of these files exist yet (Epic 04+, not built).

| File (planned) | Purpose |
|---|---|
| `create.py` | Create path — the only one with the missing-field wizard. |
| `read.py` | Read path — read-only, never writes. |
| `update.py` | Update path — direct field updates, except changing `Estado`/Status (asks "why?" first and logs a Visit). |
| `delete.py` | Delete path — always requires explicit voice confirmation before deleting. |
